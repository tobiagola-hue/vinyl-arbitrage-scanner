"""
VINYL ARBITRAGE SCANNER — scanner.py v2
Ottimizzato per girare in max 30 minuti ogni ora.
Usa solo ricerche per query (più preciso, più veloce).
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
from config import (
    MIN_SCORE, MAX_LISTINGS_PER_RELEASE,
    ACCEPTED_CONDITIONS
)

# Massimo listing da analizzare per run (per stare nei 30 min)
MAX_RESULTS_PER_QUERY   = 8    # release da esaminare per ogni query
MAX_LISTING_PER_RELEASE = 5    # listing da esaminare per release
TIER_A_ONLY_FIRST_RUN   = False


def safe_get(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def get_median(release_id: int, details: dict) -> float:
    """Estrae mediana in modo veloce senza chiamate extra se possibile."""
    # Prima prova dalla community stats (no chiamata extra)
    lp = safe_get(details, "lowest_price")
    community_have = safe_get(details, "community", "have", default=0)

    # Se il disco ha almeno 5 vendite usa il lowest price come proxy
    if lp and lp > 0 and community_have and community_have > 5:
        return float(lp) * 1.4  # stima mediana = lowest * 1.4

    # Fallback: chiama price_suggestions
    stats = dc.get_price_stats(release_id)
    if stats:
        for grade in ("Near Mint (NM or M-)", "Very Good Plus (VG+)", "Mint (M)"):
            val = safe_get(stats, grade, "value")
            if val and float(val) > 0:
                return float(val)
    return 0.0


def analyze_release(release_id: int) -> int:
    """Analizza una release. Ritorna 1 se trova opportunità, 0 altrimenti."""
    details = dc.get_release_details(release_id)
    if not details:
        return 0

    artist    = safe_get(details, "artists", default=[{}])[0].get("name", "?")
    title     = details.get("title", "?")
    label     = safe_get(details, "labels", default=[{}])[0].get("name", "")
    year      = str(details.get("year", ""))
    country   = details.get("country", "US")
    wantlist  = safe_get(details, "community", "want", default=0)
    for_sale  = details.get("num_for_sale", 0)
    notes     = details.get("notes", "")

    # Salta se troppo comune (pochi want = non vale)
    if wantlist < 50:
        return 0

    median = get_median(release_id, details)
    if median <= 0:
        return 0

    # Listing attivi
    listings_data = dc.get_marketplace_listings(release_id)
    if not listings_data:
        return 0

    listings = listings_data.get("listings", [])[:MAX_LISTING_PER_RELEASE]
    found = 0

    for listing in listings:
        listing_id = str(listing.get("id", ""))
        condition  = safe_get(listing, "condition", default="")
        price      = safe_get(listing, "price", "value", default=0) or 0
        seller     = listing.get("seller", {})
        ships_from = listing.get("ships_from", "US")
        comments   = listing.get("comments", "")

        if opportunity_exists(listing_id):
            continue

        ok, reason = passes_prefilter(listing, median)
        if not ok:
            continue

        full_text    = f"{comments} {artist} {title} {label} {notes}".lower()
        rarity_sigs  = find_rarity_signals(full_text)
        flags        = find_red_flags(full_text)

        # Scarta se ha red flag e nessun segnale rarità
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
            "seller_rating":   safe_get(seller, "stats", "rating", default=0),
            "seller_reviews":  safe_get(seller, "stats", "total", default=0),
            "listing_url":     f"https://www.discogs.com/sell/item/{listing_id}",
        }

        opp["score"] = score_opportunity(opp)
        save_opportunity(opp)

        print(
            f"    💿 {artist} — {title} | "
            f"€{price:.0f} vs €{median:.0f} mediana | "
            f"ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10"
        )

        if opp["score"] >= MIN_SCORE:
            if send_opportunity_alert(opp):
                mark_alerted(listing_id)
                found += 1
                print(f"    ✅ ALERT INVIATO — Score {opp['score']}/10")
            time.sleep(1)

    return found


def scan_query(query: str, name: str, tier: str) -> int:
    """Cerca release tramite query e analizza le prime N."""
    print(f"\n🔎 [{tier}] {name}")

    results = dc.search_releases(query=query, page=1)
    if not results:
        print(f"    Nessun risultato")
        return 0

    releases = results.get("results", [])[:MAX_RESULTS_PER_QUERY]
    found = 0

    for r in releases:
        rid = r.get("id")
        if not rid:
            continue

        artist_title = f"{r.get('title', '?')}"
        print(f"  → {artist_title}")

        try:
            found += analyze_release(rid)
        except Exception as e:
            print(f"    ⚠️ Errore su release {rid}: {e}")
            continue

        time.sleep(0.5)  # Piccola pausa tra release

    return found


def main():
    print("=" * 55)
    print("🎵 VINYL ARBITRAGE SCANNER v2 — Avvio")
    print("=" * 55)

    init_db()
    send_startup_message()

    total_found = 0

    # Ordine: prima Tier A, poi B, poi C
    for tier in ("A", "B", "C"):
        entries = [e for e in WATCHLIST if e.get("tier") == tier]
        print(f"\n{'='*20} TIER {tier} — {len(entries)} ricerche {'='*20}")

        for entry in entries:
            try:
                found = scan_query(
                    query=entry.get("query", ""),
                    name=entry.get("name", "?"),
                    tier=tier
                )
                total_found += found
            except Exception as e:
                print(f"  ❌ Errore su {entry.get('name')}: {e}")
                continue

            time.sleep(1)  # Pausa tra query

    # ── Sommario finale ────────────────────────────────
    today  = get_today_stats()
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
