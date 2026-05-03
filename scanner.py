"""
VINYL ARBITRAGE SCANNER — scanner.py v6
Nuova strategia: confronta lowest_price vs mediana (price_suggestions).
Non usa più /marketplace/search (richiede OAuth).
Quando lowest_price < 62% mediana → opportunità → alert Telegram.
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
    find_red_flags, detect_first_press_from_matrix, detect_engineer_initials
)
from telegram_alerts import (
    send_opportunity_alert, send_daily_summary,
    send_error_alert, send_startup_message
)
from watchlist import WATCHLIST
from config import (
    MIN_SCORE, MIN_MEDIAN_EUR, MAX_PRICE_RATIO,
    MIN_PROFIT_EUR, MIN_ROI, ACCEPTED_CONDITIONS
)

MAX_RESULTS_PER_QUERY = 8
MIN_WANTLIST          = 20
MIN_FOR_SALE          = 1   # Deve esserci almeno 1 in vendita


def safe_get(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def get_artist_name(details: dict) -> str:
    artists = details.get("artists") or []
    if artists:
        return artists[0].get("name", "?")
    title = details.get("title", "?")
    return title.split(" - ")[0] if " - " in title else "?"


def get_label_name(details: dict) -> str:
    labels = details.get("labels") or []
    return labels[0].get("name", "") if labels else ""


def get_median_from_suggestions(suggestions: dict) -> tuple:
    """
    Estrae mediana e condizione migliore dai price_suggestions.
    Ritorna (mediana, condizione_reference).
    """
    priority = [
        "Near Mint (NM or M-)",
        "Very Good Plus (VG+)",
        "Mint (M)",
        "Very Good (VG)",
    ]
    for condition in priority:
        val = safe_get(suggestions, condition, "value")
        if val and float(val) > 0:
            return float(val), condition
    return 0.0, ""


def analyze_release(release_id: int) -> int:
    """
    Analizza una release confrontando lowest_price vs mediana.
    Se lowest_price < MAX_PRICE_RATIO * mediana → opportunità.
    """
    try:
        details = dc.get_release_details(release_id)
        if not details:
            return 0

        artist    = get_artist_name(details)
        title     = details.get("title", "?")
        label     = get_label_name(details)
        year      = str(details.get("year", ""))
        country   = details.get("country", "US")
        wantlist  = safe_get(details, "community", "want", default=0) or 0
        for_sale  = details.get("num_for_sale", 0) or 0
        lowest    = details.get("lowest_price") or 0
        notes     = details.get("notes", "") or ""

        # ── Filtri rapidi ────────────────────────────────
        if wantlist < MIN_WANTLIST:
            print(f"      ↳ Skip: want={wantlist} < {MIN_WANTLIST}")
            return 0

        if for_sale < MIN_FOR_SALE:
            print(f"      ↳ Skip: nessuno in vendita")
            return 0

        if not lowest or float(lowest) <= 0:
            print(f"      ↳ Skip: lowest_price non disponibile")
            return 0

        lowest = float(lowest)

        # ── Mediana da price_suggestions ─────────────────
        suggestions = dc.get_price_suggestions(release_id)
        if not suggestions:
            print(f"      ↳ Skip: price_suggestions non disponibile")
            return 0

        median, ref_condition = get_median_from_suggestions(suggestions)

        if median <= 0:
            print(f"      ↳ Skip: mediana zero")
            return 0

        if median < MIN_MEDIAN_EUR:
            print(f"      ↳ Skip: mediana €{median:.0f} < soglia €{MIN_MEDIAN_EUR}")
            return 0

        ratio = lowest / median
        print(
            f"      ↳ want={wantlist} | "
            f"lowest=€{lowest:.0f} | mediana=€{median:.0f} | "
            f"ratio={ratio:.0%} | in vendita={for_sale}"
        )

        # ── Verifica se è un'opportunità ─────────────────
        if ratio > MAX_PRICE_RATIO:
            print(f"      ↳ Skip: prezzo troppo vicino alla mediana ({ratio:.0%})")
            return 0

        # ── ID opportunità = release_id (non listing_id) ─
        opp_id = f"release_{release_id}"
        if opportunity_exists(opp_id):
            print(f"      ↳ Già analizzata")
            return 0

        # ── Analisi rarità dal testo ──────────────────────
        full_text   = f"{artist} {title} {label} {notes}".lower()
        rarity_sigs = find_rarity_signals(full_text)
        flags       = find_red_flags(full_text)

        if detect_first_press_from_matrix(notes):
            rarity_sigs.append("first press (matrix detected)")
        for eng in detect_engineer_initials(notes):
            rarity_sigs.append(f"engineer: {eng}")

        # ── Calcolo profitto (usa lowest_price come prezzo acquisto) ──
        profit_data = calc_profit(lowest, median, ref_condition, country)

        if profit_data["gross_profit"] < MIN_PROFIT_EUR:
            print(f"      ↳ Skip: profitto netto €{profit_data['gross_profit']:.0f} < €{MIN_PROFIT_EUR}")
            return 0

        if profit_data["roi"] < MIN_ROI:
            print(f"      ↳ Skip: ROI {profit_data['roi']*100:.0f}% < {MIN_ROI*100:.0f}%")
            return 0

        # ── Costruisce opportunità ────────────────────────
        opp = {
            "listing_id":      opp_id,
            "source":          "discogs",
            "release_id":      str(release_id),
            "artist":          artist,
            "title":           title,
            "label":           label,
            "year":            year,
            "country":         country,
            "condition":       f"{ref_condition} (stimata)",
            "listing_price":   lowest,
            "median_price":    median,
            "est_sell_price":  profit_data["est_sell_price"],
            "gross_profit":    profit_data["gross_profit"],
            "roi":             profit_data["roi"],
            "rarity_signals":  rarity_sigs,
            "red_flags":       flags,
            "wantlist_count":  wantlist,
            "num_for_sale":    for_sale,
            "seller_username": "vedi link",
            "seller_rating":   100,
            "seller_reviews":  999,
            "listing_url":     dc.get_marketplace_url(release_id),
        }

        opp["score"] = score_opportunity(opp)
        save_opportunity(opp)

        print(
            f"    💎 {artist} — {title} | "
            f"€{lowest:.0f} vs €{median:.0f} | "
            f"ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10"
        )

        if opp["score"] >= MIN_SCORE:
            if send_opportunity_alert(opp):
                mark_alerted(opp_id)
                print(f"    ✅ ALERT INVIATO — Score {opp['score']}/10")
                time.sleep(1)
            return 1

        return 0

    except Exception as e:
        print(f"    ⚠️ Errore release {release_id}: {e}")
        return 0


def scan_query(query: str, name: str, tier: str) -> int:
    print(f"\n🔎 [{tier}] {name}")
    results = dc.search_releases(query=query)
    if not results:
        print(f"    Nessun risultato")
        return 0

    releases = (results.get("results") or [])[:MAX_RESULTS_PER_QUERY]
    if not releases:
        print(f"    Lista vuota")
        return 0

    found = 0
    for r in releases:
        rid = r.get("id")
        if not rid:
            continue
        print(f"  → {r.get('title', '?')} [{rid}]")
        found += analyze_release(rid)
        time.sleep(0.8)

    return found


def main():
    print("=" * 55)
    print("🎵 VINYL ARBITRAGE SCANNER v6 — Avvio")
    print("=" * 55)
    print("Strategia: lowest_price vs price_suggestions mediana")
    print("=" * 55)

    init_db()
    send_startup_message()

    total_found = 0
    for tier in ("A", "B", "C"):
        entries = [e for e in WATCHLIST if e.get("tier") == tier]
        print(f"\n{'='*20} TIER {tier} — {len(entries)} ricerche {'='*20}")
        for entry in entries:
            try:
                found = scan_query(entry["query"], entry["name"], tier)
                total_found += found
            except Exception as e:
                print(f"  ❌ {entry.get('name')}: {e}")
            time.sleep(1)

    today   = get_today_stats()
    alltime = get_all_time_stats()

    print("\n" + "=" * 55)
    print(f"✅ Scan completato — v6 (lowest_price strategy)")
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
        print(f"\n❌ ERRORE CRITICO:\n{traceback.format_exc()}")
        send_error_alert(str(e))
