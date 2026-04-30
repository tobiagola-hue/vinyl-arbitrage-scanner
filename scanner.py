"""
VINYL ARBITRAGE SCANNER — Main Scanner
Scansiona Discogs marketplace e identifica opportunità di arbitraggio.
Chiamato da GitHub Actions ogni 3 ore.
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
    find_red_flags, passes_prefilter, detect_first_press_from_matrix,
    detect_engineer_initials
)
from telegram_alerts import (
    send_opportunity_alert, send_daily_summary,
    send_error_alert, send_startup_message
)
from watchlist import WATCHLIST
from config import (
    MIN_SCORE, MAX_RELEASES_PER_ARTIST,
    MAX_LISTINGS_PER_RELEASE, ACCEPTED_CONDITIONS
)


# ─────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────

def safe_get(d: dict, *keys, default=None):
    """Naviga un dict annidato in modo sicuro."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def extract_price(listing: dict) -> float:
    return safe_get(listing, "price", "value", default=0) or 0


def extract_condition(listing: dict) -> str:
    return safe_get(listing, "condition", default="") or ""


def get_median_for_release(release_id: int, release_details: dict) -> float:
    """
    Estrae la mediana di prezzo dal listing Discogs.
    Usa community.lowest_price e statistics se disponibili.
    """
    stats = dc.get_price_stats(release_id)
    if stats:
        for grade in ("Mint (M)", "Near Mint (NM or M-)", "Very Good Plus (VG+)"):
            val = safe_get(stats, grade, "value")
            if val and val > 0:
                return float(val)

    # Fallback: lowest_price dalla community
    lp = safe_get(release_details, "lowest_price")
    if lp and lp > 0:
        return float(lp)

    # Fallback 2: calcola media dai listing attivi
    listings_data = dc.get_marketplace_listings(release_id)
    if listings_data:
        prices = [
            extract_price(l) for l in listings_data.get("listings", [])[:20]
            if extract_price(l) > 0
        ]
        if prices:
            return round(sum(prices) / len(prices), 2)

    return 0.0


# ─────────────────────────────────────────────
# ANALISI SINGOLA RELEASE
# ─────────────────────────────────────────────

def analyze_release(release_id: int, artist_name: str = "", title: str = "") -> int:
    """
    Analizza una release specifica su Discogs.
    Ritorna il numero di opportunità trovate.
    """
    details = dc.get_release_details(release_id)
    if not details:
        return 0

    # Dati release
    actual_artist = safe_get(details, "artists", default=[{}])[0].get("name", artist_name)
    actual_title  = details.get("title", title)
    label_name    = safe_get(details, "labels", default=[{}])[0].get("name", "")
    year          = str(details.get("year", ""))
    country       = details.get("country", "US")
    community     = details.get("community", {})
    wantlist      = community.get("want", 0)
    num_for_sale  = details.get("num_for_sale", 0)
    notes         = details.get("notes", "")

    # Prima press / engineer dal dead wax
    is_first_press = detect_first_press_from_matrix(notes)
    engineers      = detect_engineer_initials(notes)

    # Mediana prezzi
    median = get_median_for_release(release_id, details)
    if median <= 0:
        return 0

    # Listing attivi in vendita
    listings_data = dc.get_marketplace_listings(release_id)
    if not listings_data:
        return 0

    listings = listings_data.get("listings", [])[:MAX_LISTINGS_PER_RELEASE]
    found = 0

    for listing in listings:
        listing_id  = str(listing.get("id", ""))
        condition   = extract_condition(listing)
        price       = extract_price(listing)
        seller      = listing.get("seller", {})
        seller_name = seller.get("username", "")
        rating_data = seller.get("stats", {})
        rating      = rating_data.get("rating", 0)
        num_reviews = rating_data.get("total", 0)
        listing_url = f"https://www.discogs.com/sell/item/{listing_id}"
        comments    = listing.get("comments", "")
        ships_from  = listing.get("ships_from", "US")

        # Skip se già nel db
        if opportunity_exists(listing_id):
            continue

        # ── Pre-filtro rapido ──────────────────────────
        ok, reason = passes_prefilter(listing, median)
        if not ok:
            continue

        # ── Analisi testo + rarità ─────────────────────
        full_text     = f"{comments} {actual_artist} {actual_title} {label_name} {notes}".lower()
        rarity_sigs   = find_rarity_signals(full_text)
        flags         = find_red_flags(full_text)

        # Aggiungi segnali strutturati
        if is_first_press:
            rarity_sigs.append("first press (matrix A1/B1 detected)")
        for eng in engineers:
            rarity_sigs.append(f"mastering engineer: {eng}")

        # ── Calcolo economico ──────────────────────────
        profit_data = calc_profit(price, median, condition, ships_from)
        if profit_data["roi"] < 0 or profit_data["gross_profit"] < 0:
            continue

        # ── Costruisce l'opportunità ──────────────────
        opp = {
            "listing_id":      listing_id,
            "source":          "discogs",
            "release_id":      str(release_id),
            "artist":          actual_artist,
            "title":           actual_title,
            "label":           label_name,
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
            "num_for_sale":    num_for_sale,
            "seller_username": seller_name,
            "seller_rating":   rating,
            "seller_reviews":  num_reviews,
            "listing_url":     listing_url,
        }

        # ── Score finale ───────────────────────────────
        opp["score"] = score_opportunity(opp)

        # ── Salva sempre nel DB ────────────────────────
        save_opportunity(opp)

        print(
            f"  📀 {actual_artist} — {actual_title} | "
            f"€{price:.0f} (mediana €{median:.0f}) | "
            f"ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10"
        )

        # ── Alert Telegram se score >= soglia ─────────
        if opp["score"] >= MIN_SCORE:
            if send_opportunity_alert(opp):
                mark_alerted(listing_id)
                found += 1
                print(f"  ✅ ALERT INVIATO! Score {opp['score']}/10")
            time.sleep(2)  # Evita flood Telegram

    return found


# ─────────────────────────────────────────────
# SCAN PER ARTISTA
# ─────────────────────────────────────────────

def scan_artist(artist_id: int, artist_name: str, tier: str) -> int:
    print(f"\n🎤 [{tier}] {artist_name} (ID: {artist_id})")
    releases_data = dc.get_artist_releases(artist_id, per_page=MAX_RELEASES_PER_ARTIST)
    if not releases_data:
        return 0

    found = 0
    releases = releases_data.get("releases", [])

    for rel in releases:
        # Salta singoli, compilation e non-vinyl
        rtype  = rel.get("type", "")
        role   = rel.get("role", "")
        format_list = rel.get("format", "")

        if rtype == "master":
            master_id = rel.get("id")
            print(f"  🔍 Master: {rel.get('title', '?')} ({rel.get('year', '?')})")
            versions = dc.get_master_versions(master_id)
            if versions:
                for v in versions.get("versions", [])[:8]:
                    v_id = v.get("id")
                    if v_id:
                        found += analyze_release(v_id, artist_name, rel.get("title", ""))
        elif rel.get("id"):
            found += analyze_release(rel["id"], artist_name, rel.get("title", ""))

    return found


# ─────────────────────────────────────────────
# SCAN PER QUERY LIBERA
# ─────────────────────────────────────────────

def scan_search_query(query: str, name: str, tier: str) -> int:
    print(f"\n🔎 [{tier}] Query: '{name}'")
    results = dc.search_releases(query=query)
    if not results:
        return 0

    found = 0
    for result in results.get("results", [])[:15]:
        rid = result.get("id")
        if rid:
            found += analyze_release(rid)
    return found


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 55)
    print("🎵 VINYL ARBITRAGE SCANNER — Avvio")
    print("=" * 55)

    init_db()
    send_startup_message()

    total_found  = 0
    total_scanned = 0

    try:
        for entry in WATCHLIST:
            tier  = entry.get("tier", "C")
            etype = entry.get("type", "artist")
            name  = entry.get("name", "?")

            try:
                if etype == "artist":
                    found = scan_artist(entry["id"], name, tier)
                elif etype == "search":
                    found = scan_search_query(entry["query"], name, tier)
                else:
                    found = 0

                total_found   += found
                total_scanned += 1

            except Exception as e:
                print(f"  ❌ Errore su {name}: {e}")
                continue

            # Piccola pausa tra entry per non stressare l'API
            time.sleep(2)

    except Exception as e:
        err = traceback.format_exc()
        print(f"\n❌ ERRORE CRITICO:\n{err}")
        send_error_alert(str(e))

    finally:
        today_stats = get_today_stats()
        all_stats   = get_all_time_stats()
        stats = {
            "scanned":        total_scanned * 10,   # stima listing analizzati
            "today_found":    today_stats["today_found"],
            "today_alerted":  today_stats["today_alerted"],
            **all_stats,
        }

        print("\n" + "=" * 55)
        print(f"✅ Scan completato")
        print(f"   Opportunità trovate oggi:  {stats['today_found']}")
        print(f"   Alert inviati oggi:        {stats['today_alerted']}")
        print(f"   Profitto storico totale:   €{stats['total_profit_eur']:.2f}")
        print("=" * 55)

        send_daily_summary(stats)


if __name__ == "__main__":
    main()
