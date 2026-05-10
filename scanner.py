"""
VINYL ARBITRAGE SCANNER v10
24 run al giorno, ogni ora.
00:00-05:59 Italia → EXPENSIVE (alto valore, mediana >€40)
06:00-23:59 Italia → MIDVALUE  (medio valore, mediana >€18)
Recap: 07:00 top3 expensive | 13:00 e 18:00 top10 midvalue
"""
import time
import traceback
from datetime import datetime, timezone, timedelta, date

import discogs_client as dc
from database import (
    init_db, opportunity_exists, save_opportunity,
    mark_alerted, get_today_stats, get_all_time_stats, get_top_opportunities
)
from scorer import (
    calc_profit, score_opportunity, find_rarity_signals,
    find_red_flags, detect_first_press_from_matrix, detect_engineer_initials
)
from telegram_alerts import (
    send_opportunity_alert, send_daily_summary, send_error_alert,
    send_startup_message, send_recap_expensive, send_recap_midvalue
)
from watchlist import WATCHLIST_EXPENSIVE, WATCHLIST_MIDVALUE
from config import MIN_SCORE, MAX_PRICE_RATIO, MIN_PROFIT_EUR, MIN_ROI

MAX_RESULTS   = 8
FALLBACK_MULT = 1.8

# Soglie per modalita
CFG = {
    "expensive": {"min_want": 20, "min_median": 70.0},
    "midvalue":  {"min_want": 15, "min_median": 45.0},
}


def italy_hour() -> int:
    """Ora italiana (UTC+1, senza ora legale — abbastanza preciso)."""
    return (datetime.now(timezone.utc) + timedelta(hours=1)).hour


def get_mode() -> str:
    """
    00-05 Italia → expensive (alto valore, notte)
    06-23 Italia → midvalue  (medio valore, giorno)
    """
    h = italy_hour()
    return "expensive" if h < 6 else "midvalue"


def check_recap() -> str | None:
    h = italy_hour()
    if h == 7:  return "expensive"
    if h == 13: return "midvalue_1300"
    if h == 18: return "midvalue_1800"
    return None


def safe_get(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def get_artist(details):
    try:
        a = details.get("artists") or []
        if a: return a[0].get("name", "?")
        t = details.get("title", "?")
        return t.split(" - ")[0].strip() if " - " in t else "?"
    except Exception:
        return "?"


def get_label(details):
    try:
        l = details.get("labels") or []
        return l[0].get("name", "") if l else ""
    except Exception:
        return ""


def get_median(release_id, lowest):
    sugg = dc.get_price_suggestions(release_id)
    if sugg and isinstance(sugg, dict):
        for cond in ("Near Mint (NM or M-)", "Very Good Plus (VG+)", "Mint (M)", "Very Good (VG)"):
            try:
                v = safe_get(sugg, cond, "value")
                if v and float(v) > 0:
                    return float(v), cond
            except Exception:
                continue
    if lowest and float(lowest) > 0:
        return round(float(lowest) * FALLBACK_MULT, 2), "Very Good Plus (VG+)"
    return 0.0, ""


def get_best_listing(release_id):
    res = {"price": 0.0, "condition": "", "listing_id": "",
           "seller": "vedi link", "rating": 100.0, "reviews": 0, "ships_from": "EU"}
    try:
        listings = dc.get_marketplace_listings(release_id)
        if not listings:
            return res
        first = listings[0]
        p = first.get("price") or 0
        res["price"]      = float(p.get("value", 0) if isinstance(p, dict) else p or 0)
        res["condition"]  = first.get("condition", "") or ""
        res["listing_id"] = str(first.get("id", "") or "")
        s = first.get("seller") or {}
        res["seller"]     = s.get("username", "vedi link") or "vedi link"
        res["rating"]     = float(safe_get(s, "stats", "rating") or 100)
        res["reviews"]    = int(safe_get(s, "stats", "total") or 0)
        res["ships_from"] = first.get("ships_from", "EU") or "EU"
    except Exception:
        pass
    return res


def analyze(release_id, mode):
    try:
        det = dc.get_release_details(release_id)
        if not det:
            return 0

        artist  = get_artist(det)
        title   = det.get("title", "?") or "?"
        label   = get_label(det)
        year    = str(det.get("year", "") or "")
        country = det.get("country", "EU") or "EU"
        notes   = det.get("notes", "") or ""

        try: want = int(safe_get(det, "community", "want", default=0) or 0)
        except Exception: want = 0
        try: sale = int(det.get("num_for_sale", 0) or 0)
        except Exception: sale = 0
        try: lowest = float(det.get("lowest_price", 0) or 0)
        except Exception: lowest = 0.0

        cfg = CFG[mode]

        if want < cfg["min_want"]:
            print(f"      Skip want={want}")
            return 0
        if sale < 1:
            print(f"      Skip: nessuno in vendita")
            return 0
        if lowest <= 0:
            print(f"      Skip: prezzo mancante")
            return 0

        median, ref_cond = get_median(release_id, lowest)
        if median < cfg["min_median"]:
            print(f"      Skip: mediana €{median:.0f} < €{cfg['min_median']}")
            return 0

        ratio = lowest / median if median > 0 else 1.0
        print(f"      want={want} | €{lowest:.0f}/€{median:.0f} | {ratio:.0%} | sale={sale}")

        if ratio > MAX_PRICE_RATIO:
            print(f"      Skip: ratio {ratio:.0%}")
            return 0

        opp_id = f"{mode}_{release_id}_{date.today().isoformat()}"
        if opportunity_exists(opp_id):
            return 0

        lst        = get_best_listing(release_id)
        buy_price  = lst["price"] if lst["price"] > 0 else lowest
        condition  = lst["condition"] if lst["condition"] else ref_cond
        lid        = lst["listing_id"]

        buy_url     = (f"https://www.discogs.com/sell/item/{lid}"
                       if lid else dc.get_marketplace_url(release_id))
        release_url = dc.get_release_url(release_id)

        text = f"{artist} {title} {label} {notes}".lower()
        rsigs = find_rarity_signals(text)
        flags = find_red_flags(text)
        try:
            if detect_first_press_from_matrix(notes): rsigs.append("first press (matrix)")
            for e in detect_engineer_initials(notes): rsigs.append(f"engineer: {e}")
        except Exception:
            pass

        try: pdata = calc_profit(buy_price, median, condition, lst["ships_from"])
        except Exception: return 0

        if pdata.get("gross_profit", 0) < MIN_PROFIT_EUR:
            print(f"      Skip: profitto €{pdata.get('gross_profit',0):.0f}")
            return 0
        if pdata.get("roi", 0) < MIN_ROI:
            print(f"      Skip: ROI {pdata.get('roi',0)*100:.0f}%")
            return 0

        opp = {
            "listing_id":      opp_id,
            "source":          "discogs",
            "mode":            mode,
            "release_id":      str(release_id),
            "artist":          artist,
            "title":           title,
            "label":           label,
            "year":            year,
            "country":         country,
            "condition":       condition,
            "listing_price":   buy_price,
            "median_price":    median,
            "est_sell_price":  pdata.get("est_sell_price", 0),
            "gross_profit":    pdata.get("gross_profit", 0),
            "roi":             pdata.get("roi", 0),
            "rarity_signals":  rsigs,
            "red_flags":       flags,
            "wantlist_count":  want,
            "num_for_sale":    sale,
            "seller_username": lst["seller"],
            "seller_rating":   lst["rating"],
            "seller_reviews":  lst["reviews"],
            "listing_url":     buy_url,
            "release_url":     release_url,
        }

        try: opp["score"] = score_opportunity(opp)
        except Exception: opp["score"] = 5.0

        save_opportunity(opp)
        print(f"    {artist} — {title} | €{buy_price:.0f}->€{median:.0f} | ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10")

        if opp["score"] >= MIN_SCORE:
            try:
                if send_opportunity_alert(opp):
                    mark_alerted(opp_id)
                    print(f"    ALERT — Score {opp['score']}/10")
                    time.sleep(2)
            except Exception as e:
                print(f"    Telegram: {e}")
            return 1
        return 0

    except Exception as e:
        print(f"    Errore {release_id}: {e}")
        return 0


def scan_query(query, name, mode):
    print(f"\n  [{name}]")
    try:
        res = dc.search_releases(query=query)
    except Exception as e:
        print(f"    Search error: {e}")
        return 0
    if not res:
        return 0
    releases = (res.get("results") or [])[:MAX_RESULTS]
    found = 0
    for r in releases:
        try:
            rid = r.get("id")
            if not rid: continue
            print(f"  -> {r.get('title','?')} [{rid}]")
            found += analyze(rid, mode)
        except Exception as e:
            print(f"    Err: {e}")
        time.sleep(0.8)
    return found


def main():
    mode      = get_mode()
    h         = italy_hour()
    recap     = check_recap()
    watchlist = WATCHLIST_EXPENSIVE if mode == "expensive" else WATCHLIST_MIDVALUE

    print("=" * 55)
    print(f"VINYL ARBITRAGE v10 | Ora IT: {h}:xx | Modo: {mode.upper()}")
    print("=" * 55)

    init_db()
    send_startup_message(mode)

    # Recap automatici
    if recap == "expensive":
        print("\nRecap 07:00 — Alto Valore")
        top = get_top_opportunities("expensive", limit=3, days=1)
        send_recap_expensive(top)
    elif recap == "midvalue_1300":
        print("\nRecap 13:00 — Medio Valore")
        top = get_top_opportunities("midvalue", limit=10, days=1)
        send_recap_midvalue(top, slot="13:00")
    elif recap == "midvalue_1800":
        print("\nRecap 18:00 — Medio Valore")
        top = get_top_opportunities("midvalue", limit=10, days=1)
        send_recap_midvalue(top, slot="18:00")

    # Scansione
    print(f"\nScansione {len(watchlist)} query...")
    for entry in watchlist:
        try:
            scan_query(entry.get("query", ""), entry.get("name", "?"), mode)
        except Exception as e:
            print(f"  Errore {entry.get('name','?')}: {e}")
        time.sleep(1)

    today   = get_today_stats()
    alltime = get_all_time_stats()
    print(f"\nFine | Trovate: {today['today_found']} | Alert: {today['today_alerted']}")
    send_daily_summary({
        "scanned":       len(watchlist) * MAX_RESULTS,
        "today_found":   today["today_found"],
        "today_alerted": today["today_alerted"],
        **alltime,
    })


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrotto")
    except Exception as e:
        print(f"\nERRORE:\n{traceback.format_exc()}")
        try: send_error_alert(str(e)[:500])
        except Exception: pass
