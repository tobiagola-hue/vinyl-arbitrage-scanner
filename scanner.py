"""
VINYL ARBITRAGE SCANNER v12
00-05 Italia → EXPENSIVE: Discogs VG+ listing vs VG+ median
06-23 Italia → MIDVALUE:  eBay listing vs Discogs median
Recap: 07:00 top3 expensive | 13:00 e 18:00 top10 midvalue
"""
import time, traceback
from datetime import datetime, timezone, timedelta, date

import discogs_client as dc
import ebay_client as ec
from database import (
    init_db, opportunity_exists, save_opportunity,
    mark_alerted, get_today_stats, get_all_time_stats, get_top_opportunities
)
from scorer import (
    calc_profit, score_opportunity,
    find_rarity_signals, find_red_flags,
    detect_first_press_from_matrix, detect_engineer_initials
)
from telegram_alerts import (
    send_opportunity_alert, send_daily_summary, send_error_alert,
    send_startup_message, send_recap_expensive, send_recap_midvalue
)
from watchlist import WATCHLIST_EXPENSIVE, WATCHLIST_MIDVALUE
from config import (
    MIN_SCORE, MIN_PROFIT_EUR, MIN_ROI,
    MAX_RATIO_EXPENSIVE, MIN_MEDIAN_EXPENSIVE, MIN_WANT_EXPENSIVE,
    MAX_RATIO_MIDVALUE,  MIN_MEDIAN_MIDVALUE,  MIN_WANT_MIDVALUE,
)

MAX_RESULTS = 8


def italy_hour():
    return (datetime.now(timezone.utc) + timedelta(hours=1)).hour


def get_mode():
    return "expensive" if italy_hour() < 6 else "midvalue"


def check_recap():
    h = italy_hour()
    if h == 7:  return "expensive"
    if h == 13: return "midvalue_1300"
    if h == 18: return "midvalue_1800"
    return None


def sg(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict): return default
        d = d.get(k, default)
    return d


def get_artist(d):
    try:
        a = d.get("artists") or []
        if a: return a[0].get("name","?")
        t = d.get("title","?")
        return t.split(" - ")[0].strip() if " - " in t else "?"
    except Exception: return "?"


def get_label(d):
    try:
        l = d.get("labels") or []
        return l[0].get("name","") if l else ""
    except Exception: return ""


def get_vgplus_median(release_id):
    sugg = dc.get_price_suggestions(release_id)
    if not sugg: return 0.0
    vgp = sg(sugg, "Very Good Plus (VG+)", "value")
    if vgp and float(vgp) > 0: return float(vgp)
    nm = sg(sugg, "Near Mint (NM or M-)", "value")
    if nm and float(nm) > 0: return round(float(nm)*0.85, 2)
    mint = sg(sugg, "Mint (M)", "value")
    if mint and float(mint) > 0: return round(float(mint)*0.75, 2)
    return 0.0


def get_cheapest_vgplus(release_id):
    listings = dc.get_marketplace_listings(release_id)
    if not listings: return None
    best = None
    best_price = float("inf")
    for lst in listings:
        cond = lst.get("condition","") or ""
        if cond not in ["Mint (M)","Near Mint (NM or M-)","Very Good Plus (VG+)"]:
            continue
        p = lst.get("price") or 0
        price = float(p.get("value",0) if isinstance(p,dict) else p or 0)
        if price <= 0 or price >= best_price: continue
        best_price = price
        s = lst.get("seller") or {}
        best = {
            "price":     price,
            "condition": cond,
            "listing_id": str(lst.get("id","") or ""),
            "seller":    s.get("username","vedi link") or "vedi link",
            "rating":    float(sg(s,"stats","rating") or 100),
            "reviews":   int(sg(s,"stats","total") or 0),
            "ships_from": lst.get("ships_from","EU") or "EU",
        }
    return best


# ─── EXPENSIVE: Discogs → Discogs ───────────────────────────────────────────

def analyze_expensive(release_id):
    try:
        det = dc.get_release_details(release_id)
        if not det: return 0

        artist  = get_artist(det)
        title   = det.get("title","?") or "?"
        label   = get_label(det)
        year    = str(det.get("year","") or "")
        country = det.get("country","EU") or "EU"
        notes   = det.get("notes","") or ""

        try: want = int(sg(det,"community","want",default=0) or 0)
        except Exception: want = 0
        try: sale = int(det.get("num_for_sale",0) or 0)
        except Exception: sale = 0

        if want < MIN_WANT_EXPENSIVE:
            print(f"      Skip want={want}"); return 0
        if sale < 1:
            print(f"      Skip: nessuno in vendita"); return 0

        median = get_vgplus_median(release_id)
        if median < MIN_MEDIAN_EXPENSIVE:
            print(f"      Skip: VG+ mediana €{median:.0f} < €{MIN_MEDIAN_EXPENSIVE}"); return 0

        listing = get_cheapest_vgplus(release_id)
        if not listing:
            print(f"      Skip: nessun listing VG+ trovato"); return 0

        ratio = listing["price"] / median if median > 0 else 1.0
        print(f"      want={want} | VG+ €{listing['price']:.0f} / mediana €{median:.0f} | {ratio:.0%} | sale={sale}")

        if ratio > MAX_RATIO_EXPENSIVE:
            print(f"      Skip: ratio {ratio:.0%}"); return 0

        opp_id = f"exp_{release_id}_{date.today().isoformat()}"
        if opportunity_exists(opp_id): return 0

        lid = listing["listing_id"]
        buy_url = (f"https://www.discogs.com/sell/item/{lid}"
                   if lid else dc.get_marketplace_url(release_id))

        text  = f"{artist} {title} {label} {notes}".lower()
        rsigs = find_rarity_signals(text)
        flags = find_red_flags(text)
        try:
            if detect_first_press_from_matrix(notes): rsigs.append("first press (matrix)")
            for e in detect_engineer_initials(notes): rsigs.append(f"engineer: {e}")
        except Exception: pass

        try: pdata = calc_profit(listing["price"], median, listing["condition"], listing["ships_from"])
        except Exception: return 0

        if pdata.get("gross_profit",0) < MIN_PROFIT_EUR:
            print(f"      Skip: profitto €{pdata.get('gross_profit',0):.0f}"); return 0
        if pdata.get("roi",0) < MIN_ROI:
            print(f"      Skip: ROI {pdata.get('roi',0)*100:.0f}%"); return 0

        opp = {
            "listing_id": opp_id, "source": "discogs", "mode": "expensive",
            "release_id": str(release_id), "artist": artist, "title": title,
            "label": label, "year": year, "country": country,
            "condition": listing["condition"],
            "listing_price": listing["price"], "median_price": median,
            "est_sell_price": pdata.get("est_sell_price",0),
            "gross_profit": pdata.get("gross_profit",0),
            "roi": pdata.get("roi",0),
            "rarity_signals": rsigs, "red_flags": flags,
            "wantlist_count": want, "num_for_sale": sale,
            "seller_username": listing["seller"],
            "seller_rating": listing["rating"],
            "seller_reviews": listing["reviews"],
            "listing_url": buy_url,
            "release_url": dc.get_release_url(release_id),
            "buy_site": "Discogs",
        }
        try: opp["score"] = score_opportunity(opp)
        except Exception: opp["score"] = 5.0

        save_opportunity(opp)
        print(f"    TROVATO: {artist} — {title} | €{listing['price']:.0f} vs €{median:.0f} | ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10")

        if opp["score"] >= MIN_SCORE:
            try:
                if send_opportunity_alert(opp):
                    mark_alerted(opp_id)
                    print(f"    ALERT INVIATO")
                    time.sleep(2)
            except Exception as e:
                print(f"    Telegram: {e}")
            return 1
        return 0
    except Exception as e:
        print(f"    Errore {release_id}: {e}"); return 0


# ─── MIDVALUE: eBay → Discogs ────────────────────────────────────────────────

def analyze_midvalue(entry):
    """
    Per ogni entry nella watchlist midvalue:
    1. Cerca release su Discogs → prende mediana VG+
    2. Cerca su eBay IT+UK → prende listing piu economico
    3. Se eBay price < X% mediana → opportunita
    """
    artist_hint = entry.get("artist","")
    query       = entry.get("query","")
    name        = entry.get("name","?")

    # Step 1: trova release su Discogs
    res = dc.search_releases(query=query)
    if not res: return 0

    releases = (res.get("results") or [])[:5]
    found = 0

    for r in releases:
        rid = r.get("id")
        if not rid: continue

        try:
            det = dc.get_release_details(rid)
            if not det: continue

            artist  = get_artist(det)
            title   = det.get("title","?") or "?"
            label   = get_label(det)
            year    = str(det.get("year","") or "")
            country = det.get("country","EU") or "EU"
            notes   = det.get("notes","") or ""

            try: want = int(sg(det,"community","want",default=0) or 0)
            except Exception: want = 0

            if want < MIN_WANT_MIDVALUE:
                print(f"      Skip want={want}"); continue

            # Step 2: mediana VG+ da Discogs
            median = get_vgplus_median(rid)
            if median < MIN_MEDIAN_MIDVALUE:
                print(f"      Skip: mediana €{median:.0f} < €{MIN_MEDIAN_MIDVALUE}"); continue

            print(f"  -> {artist} — {title} | mediana VG+ €{median:.0f} | want={want}")

            # Step 3: cerca su eBay
            max_ebay_price = median * MAX_RATIO_MIDVALUE
            ebay = ec.find_best_ebay_listing(
                artist if artist != "?" else artist_hint,
                title,
                max_price=max_ebay_price
            )

            if not ebay:
                # Nessun listing eBay sotto soglia
                print(f"      Nessun listing eBay sotto €{max_ebay_price:.0f}")
                continue

            ratio = ebay["total"] / median if median > 0 else 1.0
            print(f"      eBay {ebay['site']}: €{ebay['total']:.0f} | ratio {ratio:.0%}")

            if ratio > MAX_RATIO_MIDVALUE:
                print(f"      Skip: ratio {ratio:.0%}"); continue

            opp_id = f"mid_{rid}_{date.today().isoformat()}"
            if opportunity_exists(opp_id): continue

            # Calcola profitto: compra eBay, vendi su Discogs
            try:
                pdata = calc_profit(ebay["total"], median, "Very Good (VG)", country)
            except Exception: continue

            if pdata.get("gross_profit",0) < MIN_PROFIT_EUR:
                print(f"      Skip: profitto €{pdata.get('gross_profit',0):.0f}"); continue
            if pdata.get("roi",0) < MIN_ROI:
                print(f"      Skip: ROI {pdata.get('roi',0)*100:.0f}%"); continue

            text  = f"{artist} {title} {label} {notes}".lower()
            rsigs = find_rarity_signals(text)
            flags = find_red_flags(text)

            opp = {
                "listing_id": opp_id, "source": "ebay", "mode": "midvalue",
                "release_id": str(rid), "artist": artist, "title": title,
                "label": label, "year": year, "country": country,
                "condition": f"Used ({ebay['condition']})",
                "listing_price": ebay["total"],
                "median_price": median,
                "est_sell_price": pdata.get("est_sell_price",0),
                "gross_profit": pdata.get("gross_profit",0),
                "roi": pdata.get("roi",0),
                "rarity_signals": rsigs, "red_flags": flags,
                "wantlist_count": want, "num_for_sale": 0,
                "seller_username": ebay.get("seller",""),
                "seller_rating": 0, "seller_reviews": 0,
                "listing_url": ebay.get("url",""),
                "release_url": dc.get_release_url(rid),
                "buy_site": ebay.get("site","eBay"),
            }
            try: opp["score"] = score_opportunity(opp)
            except Exception: opp["score"] = 5.0

            save_opportunity(opp)
            print(f"    TROVATO: {artist} — {title} | eBay €{ebay['total']:.0f} vs Discogs €{median:.0f} | ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10")

            if opp["score"] >= MIN_SCORE:
                try:
                    if send_opportunity_alert(opp):
                        mark_alerted(opp_id)
                        print(f"    ALERT INVIATO")
                        time.sleep(2)
                except Exception as e:
                    print(f"    Telegram: {e}")
                found += 1

        except Exception as e:
            print(f"    Errore release {rid}: {e}")
            continue

        time.sleep(0.8)

    return found


def scan_expensive_query(query, name):
    print(f"\n  [{name}]")
    try: res = dc.search_releases(query=query)
    except Exception as e:
        print(f"    Search error: {e}"); return 0
    if not res: return 0
    releases = (res.get("results") or [])[:MAX_RESULTS]
    found = 0
    for r in releases:
        try:
            rid = r.get("id")
            if not rid: continue
            print(f"  -> {r.get('title','?')} [{rid}]")
            found += analyze_expensive(rid)
        except Exception as e:
            print(f"    Err: {e}")
        time.sleep(0.8)
    return found


def main():
    mode  = get_mode()
    h     = italy_hour()
    recap = check_recap()

    print("="*55)
    print(f"VINYL ARBITRAGE v12 | Ora IT: {h}:xx | Modo: {mode.upper()}")
    if mode == "midvalue":
        ebay_ok = "eBay ON" if ec.is_configured() else "eBay OFF (aggiungi EBAY_APP_ID)"
        print(f"eBay status: {ebay_ok}")
    print("="*55)

    init_db()
    send_startup_message(mode)

    # Recap automatici
    if recap == "expensive":
        top = get_top_opportunities("expensive", limit=3, days=1)
        send_recap_expensive(top)
    elif recap == "midvalue_1300":
        top = get_top_opportunities("midvalue", limit=10, days=1)
        send_recap_midvalue(top, slot="13:00")
    elif recap == "midvalue_1800":
        top = get_top_opportunities("midvalue", limit=10, days=1)
        send_recap_midvalue(top, slot="18:00")

    if mode == "expensive":
        watchlist = WATCHLIST_EXPENSIVE
        print(f"\nScansione {len(watchlist)} query DISCOGS...")
        for entry in watchlist:
            try: scan_expensive_query(entry.get("query",""), entry.get("name","?"))
            except Exception as e: print(f"  Err {entry.get('name','?')}: {e}")
            time.sleep(1)
    else:
        watchlist = WATCHLIST_MIDVALUE
        print(f"\nScansione {len(watchlist)} artisti su EBAY + DISCOGS...")
        for entry in watchlist:
            try:
                print(f"\n  [{entry.get('name','?')}]")
                analyze_midvalue(entry)
            except Exception as e: print(f"  Err {entry.get('name','?')}: {e}")
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
