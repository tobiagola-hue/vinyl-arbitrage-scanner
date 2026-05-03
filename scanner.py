"""
VINYL ARBITRAGE SCANNER — scanner.py v3
Bugfix: list index out of range, search params corretti, watchlist corretta.
"""
import time
import traceback

import discogs_client as dc
from database import (
    init_db, opportunity_exists, save_opportunity,
    mark_alerted, get_today_stats, get_all_time_stats
)
from scorer import (
    calc_profit, score_opportunity, find_rarity_signals,
    find_red_flags, passes_prefilter,
    detect_first_press_from_matrix, detect_engineer_initials
)
from telegram_alerts import (
    send_opportunity_alert, send_daily_summary,
    send_error_alert, send_startup_message
)
from watchlist import WATCHLIST
from config import MIN_SCORE

MAX_RESULTS_PER_QUERY   = 8
MAX_LISTING_PER_RELEASE = 5


def safe_get(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def get_artist_name(details: dict) -> str:
    """Estrae nome artista in modo sicuro, gestisce lista vuota."""
    artists = details.get("artists") or []
    if artists and isinstance(artists, list) and len(artists) > 0:
        return artists[0].get("name", "?")
    # Fallback: prova dal titolo o dal campo extraartists
    title = details.get("title", "?")
    return title.split(" - ")[0] if " - " in title else "?"


def get_label_name(details: dict) -> str:
    """Estrae nome label in modo sicuro."""
    labels = details.get("labels") or []
    if labels and isinstance(labels, list) and len(labels) > 0:
        return labels[0].get("name", "")
    return ""


def get_median(release_id: int, details: dict) -> float:
    """Stima mediana senza chiamate extra quando possibile."""
    lp = safe_get(details, "lowest_price")
    community_have = safe_get(details, "community", "have", default=0) or 0

    if lp and float(lp) > 0 and community_have > 5:
        return round(float(lp) * 1.4, 2)

    stats = dc.get_price_stats(release_id)
    if stats:
        for grade in ("Near Mint (NM or M-)", "Very Good Plus (VG+)", "Mint (M)"):
            val = safe_get(stats, grade, "value")
            if val and float(val) > 0:
                return float(val)
    return 0.0


def analyze_release(release_id: int) -> int:
    """Analizza una release. Ritorna 1 se trova e alerta un'opportunità."""
    try:
        details = dc.get_release_details(release_id)
        if not details:
            return 0

        artist   = get_artist_name(details)
        title    = details.get("title", "?")
        label    = get_label_name(details)
        year     = str(details.get("year", ""))
        country  = details.get("country", "US")
        wantlist = safe_get(details, "community", "want", default=0) or 0
        for_sale = details.get("num_for_sale", 0) or 0
        notes    = details.get("notes", "") or ""

        if wantlist < 50:
            return 0

        median = get_median(release_id, details)
        if median <= 0:
            return 0

        listings_data = dc.get_marketplace_listings(release_id)
        if not listings_data:
            return 0

        listings = (listings_data.get("listings") or [])[:MAX_LISTING_PER_RELEASE]
        found = 0

        for listing in listings:
            listing_id = str(listing.get("id", ""))
            condition  = safe_get(listing, "condition") or ""
            price      = safe_get(listing, "price", "value") or 0
            price      = float(price)
            seller     = listing.get("seller") or {}
            ships_from = listing.get("ships_from", "US") or "US"
            comments   = listing.get("comments", "") or ""

            if opportunity_exists(listing_id):
                continue

            ok, _ = passes_prefilter(listing, median)
            if not ok:
                continue

            full_text   = f"{comments} {artist} {title} {label} {notes}".lower()
            rarity_sigs = find_rarity_signals(full_text)
            flags       = find_red_flags(full_text)

            if flags and not rarity_sigs:
                continue

            if detect_first_press_from_matrix(notes):
                rarity_sigs.append("first press (matrix detected)")
            for eng in detect_engineer_initials(notes):
                rarity_sigs.append(f"engineer: {eng}")

            profit_data = calc_profit(price, median, condition, ships_from)
            if profit_data["gross_profit"] <= 0:
                continue

            opp = {
                "listing_id":      listing_id,
                "source":          "discogs",
                "release_id":      str(release_id),
                "artist":          artist,
                "title":           title,
                "label":           label,
                "year":            year,
                "country":         country,
                "condition":       condition,
                "listing_price":   price,
                "median_price":    median,
                "est_sell_price":  profit_data["est_sell_price"],
                "gross_profit":    profit_data["gross_profit"],
                "roi":             profit_data["roi"],
                "rarity_signals":  rarity_sigs,
                "red_flags":       flags,
                "wantlist_count":  wantlist,
                "num_for_sale":    for_sale,
                "seller_username": seller.get("username", ""),
                "seller_rating":   safe_get(seller, "stats", "rating") or 0,
                "seller_reviews":  safe_get(seller, "stats", "total") or 0,
                "listing_url":     f"https://www.discogs.com/sell/item/{listing_id}",
            }

            opp["score"] = score_opportunity(opp)
            save_opportunity(opp)

            print(
                f"    💿 {artist} — {title} | "
                f"€{price:.0f} vs mediana €{median:.0f} | "
                f"ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10"
            )

            if opp["score"] >= MIN_SCORE:
                if send_opportunity_alert(opp):
                    mark_alerted(listing_id)
                    found += 1
                    print(f"    ✅ ALERT — Score {opp['score']}/10")
                time.sleep(1)

        return found

    except Exception as e:
        print(f"    ⚠️ Errore analisi release {release_id}: {e}")
        return 0


def scan_query(query: str, name: str, tier: str) -> int:
    """Cerca release per query e analizza le prime N."""
    print(f"\n🔎 [{tier}] {name}")

    results = dc.search_releases(query=query, page=1)
    if not results:
        print(f"    Nessun risultato per: {query}")
        return 0

    releases = (results.get("results") or [])[:MAX_RESULTS_PER_QUERY]
    if not releases:
        print(f"    Lista risultati vuota")
        return 0

    found = 0
    for r in releases:
        rid = r.get("id")
        if not rid:
            continue
        print(f"  → {r.get('title', '?')} [{rid}]")
        found += analyze_release(rid)
        time.sleep(0.5)

    return found


def main():
    print("=" * 55)
    print("🎵 VINYL ARBITRAGE SCANNER v3 — Avvio")
    print("=" * 55)

    init_db()
    send_startup_message()

    total_found = 0

    for tier in ("A", "B", "C"):
        entries = [e for e in WATCHLIST if e.get("tier") == tier]
        print(f"\n{'='*20} TIER {tier} — {len(entries)} ricerche {'='*20}")

        for entry in entries:
            try:
                if entry.get("type") == "search":
                    found = scan_query(
                        query=entry["query"],
                        name=entry["name"],
                        tier=tier
                    )
                    total_found += found
                else:
                    print(f"  ⚠️ Tipo non supportato: {entry.get('type')}")
            except Exception as e:
                print(f"  ❌ Errore su {entry.get('name')}: {e}")
                continue
            time.sleep(1)

    today   = get_today_stats()
    alltime = get_all_time_stats()

    print("\n" + "=" * 55)
    print(f"✅ Scan completato")
    print(f"   Opportunità oggi:   {today['today_found']}")
    print(f"   Alert inviati oggi: {today['today_alerted']}")
    print(f"   Profitto storico:   €{alltime['total_profit_eur']:.2f}")
    print("=" * 55)

    send_daily_summary({
        "scanned":       len(WATCHLIST) * MAX_RESULTS_PER_QUERY,
        "today_found":   today["today_found"],
        "today_alerted": today["today_alerted"],
        **alltime,
    })


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err = traceback.format_exc()
        print(f"\n❌ ERRORE CRITICO:\n{err}")
        send_error_alert(str(e))
