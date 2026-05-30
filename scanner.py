"""
VINYL ARBITRAGE SCANNER v16
Fix: rimosso dedup 7gg aggressivo, startup solo mezzanotte,
riassunto silenzioso, eBay UK prima di IT.
"""
import time, traceback
from datetime import datetime, timezone, timedelta, date

import discogs_client as dc
import ebay_client as ec
from database import (
    init_db, opportunity_exists, save_opportunity,
    get_today_stats, get_all_time_stats, get_top_opportunities
)
from scorer import (
    calc_profit, score_opportunity,
    find_rarity_signals, find_red_flags,
    detect_first_press_from_matrix, detect_engineer_initials
)
from telegram_alerts import (
    send_daily_recap, send_daily_summary,
    send_error_alert, send_startup_message
)
from watchlist import WATCHLIST_EXPENSIVE, get_midvalue_watchlist
from config import (
    MIN_PROFIT_EUR, MIN_ROI,
    MAX_RATIO_EXPENSIVE, MIN_MEDIAN_EXPENSIVE, MIN_WANT_EXPENSIVE,
    MAX_RATIO_MIDVALUE, MIN_MEDIAN_MIDVALUE, MIN_WANT_MIDVALUE,
)

MAX_DISC = 5


def italy_now():
    return datetime.now(timezone.utc) + timedelta(hours=1)

def italy_hour():   return italy_now().hour
def italy_minute(): return italy_now().minute
def get_mode():     return "expensive" if italy_hour() < 6 else "midvalue"

def is_recap_time():
    h, m = italy_hour(), italy_minute()
    return h == 4 and 30 <= m < 59

def is_first_run():
    return italy_hour() == 0 and italy_minute() < 35


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
    for cond in ("Very Good Plus (VG+)", "Near Mint (NM or M-)", "Mint (M)"):
        v = sg(sugg, cond, "value")
        if v and float(v) > 0:
            mult = 0.85 if "Near Mint" in cond else 0.75 if "Mint" in cond else 1.0
            return round(float(v)*mult, 2)
    return 0.0

def get_ref_price(det):
    try:
        lp = float(det.get("lowest_price") or 0)
        if lp > 0: return round(lp*1.5, 2)
    except Exception: pass
    return 0.0

def get_cheapest_vgplus(release_id):
    listings = dc.get_marketplace_listings(release_id)
    if not listings: return None
    best = None; best_p = float("inf")
    for lst in listings:
        cond = lst.get("condition","") or ""
        if cond not in ["Mint (M)","Near Mint (NM or M-)","Very Good Plus (VG+)"]: continue
        p = lst.get("price") or 0
        price = float(p.get("value",0) if isinstance(p,dict) else p or 0)
        if price <= 0 or price >= best_p: continue
        best_p = price
        s = lst.get("seller") or {}
        best = {
            "price": price, "condition": cond,
            "listing_id": str(lst.get("id","") or ""),
            "seller": s.get("username","vedi link") or "vedi link",
            "rating": float(sg(s,"stats","rating") or 100),
            "reviews": int(sg(s,"stats","total") or 0),
            "ships_from": lst.get("ships_from","EU") or "EU",
        }
    return best


def analyze_expensive(release_id):
    try:
        det = dc.get_release_details(release_id)
        if not det: return 0
        artist  = get_artist(det); title = det.get("title","?") or "?"
        label   = get_label(det);  year  = str(det.get("year","") or "")
        country = det.get("country","EU") or "EU"
        notes   = det.get("notes","") or ""
        try: want = int(sg(det,"community","want",default=0) or 0)
        except Exception: want = 0
        try: sale = int(det.get("num_for_sale",0) or 0)
        except Exception: sale = 0

        if want < MIN_WANT_EXPENSIVE: return 0
        if sale < 1: return 0

        median = get_vgplus_median(release_id)
        if median < MIN_MEDIAN_EXPENSIVE: return 0

        listing = get_cheapest_vgplus(release_id)
        if not listing: return 0

        ratio = listing["price"]/median if median > 0 else 1.0
        print(f"      want={want} | VG+ €{listing['price']:.0f}/€{median:.0f} | {ratio:.0%}")
        if ratio > MAX_RATIO_EXPENSIVE: return 0

        opp_id = f"exp_{release_id}_{date.today().isoformat()}"
        if opportunity_exists(opp_id): return 0

        lid = listing["listing_id"]
        buy_url = (f"https://www.discogs.com/sell/item/{lid}"
                   if lid else dc.get_marketplace_url(release_id))
        text = f"{artist} {title} {label} {notes}".lower()
        rsigs = find_rarity_signals(text); flags = find_red_flags(text)
        try:
            if detect_first_press_from_matrix(notes): rsigs.append("first press")
            for e in detect_engineer_initials(notes): rsigs.append(f"engineer: {e}")
        except Exception: pass

        try: pdata = calc_profit(listing["price"],median,listing["condition"],listing["ships_from"])
        except Exception: return 0
        if pdata.get("gross_profit",0) < MIN_PROFIT_EUR: return 0
        if pdata.get("roi",0) < MIN_ROI: return 0

        opp = {
            "listing_id": opp_id, "source": "discogs", "mode": "expensive",
            "release_id": str(release_id), "artist": artist, "title": title,
            "label": label, "year": year, "country": country,
            "condition": listing["condition"], "listing_price": listing["price"],
            "median_price": median, "est_sell_price": pdata.get("est_sell_price",0),
            "gross_profit": pdata.get("gross_profit",0), "roi": pdata.get("roi",0),
            "rarity_signals": rsigs, "red_flags": flags,
            "wantlist_count": want, "num_for_sale": sale,
            "seller_username": listing["seller"], "seller_rating": listing["rating"],
            "seller_reviews": listing["reviews"], "listing_url": buy_url,
            "release_url": dc.get_release_url(release_id), "buy_site": "Discogs",
        }
        try: opp["score"] = score_opportunity(opp)
        except Exception: opp["score"] = 5.0
        save_opportunity(opp)
        print(f"    SALVATO: {artist} — {title} | ROI {opp['roi']*100:.0f}% | Score {opp['score']:.1f}")
        return 1
    except Exception as e:
        print(f"    Errore {release_id}: {e}"); return 0


def analyze_midvalue_release(rid, artist_hint=""):
    try:
        det = dc.get_release_details(rid)
        if not det: return 0
        artist  = get_artist(det); title = det.get("title","?") or "?"
        label   = get_label(det);  year  = str(det.get("year","") or "")
        country = det.get("country","EU") or "EU"
        notes   = det.get("notes","") or ""
        try: want = int(sg(det,"community","want",default=0) or 0)
        except Exception: want = 0
        try: orig_year = int(det.get("year",0) or 0)
        except Exception: orig_year = 0

        if want < MIN_WANT_MIDVALUE: return 0

        ref = get_ref_price(det)
        lp  = float(det.get("lowest_price") or 0)
        if ref < MIN_MEDIAN_MIDVALUE: return 0

        print(f"  -> {artist} — {title} ({orig_year}) | lowest=€{lp:.0f} ref=€{ref:.0f} want={want}")

        opp_id = f"mid_{rid}_{date.today().isoformat()}"
        if opportunity_exists(opp_id): return 0

        search_artist = artist if artist != "?" else artist_hint
        max_ebay = ref * MAX_RATIO_MIDVALUE
        ebay = ec.find_best_listing(search_artist, title,
                                    original_year=orig_year, max_price=max_ebay)
        if not ebay: return 0

        ratio = ebay["total"]/ref if ref > 0 else 1.0
        if ratio > MAX_RATIO_MIDVALUE: return 0

        try: pdata = calc_profit(ebay["total"],ref,"Very Good (VG)",country)
        except Exception: return 0
        if pdata.get("gross_profit",0) < MIN_PROFIT_EUR: return 0
        if pdata.get("roi",0) < MIN_ROI: return 0

        text  = f"{artist} {title} {label} {notes}".lower()
        rsigs = find_rarity_signals(text); flags = find_red_flags(text)

        opp = {
            "listing_id": opp_id, "source": "ebay", "mode": "midvalue",
            "release_id": str(rid), "artist": artist, "title": title,
            "label": label, "year": year, "country": country,
            "condition": f"Used ({ebay['condition']})",
            "listing_price": ebay["total"], "median_price": ref,
            "est_sell_price": pdata.get("est_sell_price",0),
            "gross_profit": pdata.get("gross_profit",0), "roi": pdata.get("roi",0),
            "rarity_signals": rsigs, "red_flags": flags,
            "wantlist_count": want, "num_for_sale": 0,
            "seller_username": ebay.get("seller",""), "seller_rating": 0,
            "seller_reviews": 0, "listing_url": ebay.get("url",""),
            "release_url": dc.get_release_url(rid), "buy_site": ebay.get("site","eBay"),
            "notes": "incerto" if ebay.get("uncertain") else "",
        }
        try: opp["score"] = score_opportunity(opp)
        except Exception: opp["score"] = 5.0
        save_opportunity(opp)
        print(f"    SALVATO: {artist} — {title} | eBay €{ebay['total']:.0f}/ref €{ref:.0f} | ROI {opp['roi']*100:.0f}%")
        return 1
    except Exception as e:
        print(f"    Errore {rid}: {e}"); return 0


def scan_query(query, name, mode, artist_hint=""):
    print(f"\n  [{name}]")
    try: res = dc.search_releases(query=query)
    except Exception as e: print(f"    Search err: {e}"); return 0
    if not res: return 0
    releases = (res.get("results") or [])[:MAX_DISC]
    found = 0
    for r in releases:
        try:
            rid = r.get("id")
            if not rid: continue
            if mode == "expensive":
                print(f"  -> {r.get('title','?')} [{rid}]")
                found += analyze_expensive(rid)
            else:
                found += analyze_midvalue_release(rid, artist_hint)
        except Exception as e: print(f"    Err: {e}")
        time.sleep(0.8)
    return found


def main():
    mode = get_mode()
    h, m = italy_hour(), italy_minute()

    print("="*55)
    print(f"VINYL ARBITRAGE v16 | IT {h:02d}:{m:02d} | {mode.upper()}")
    print("="*55)

    init_db()

    if is_first_run():
        send_startup_message(mode)

    if is_recap_time():
        print("\nInvio recap 4:30...")
        exp = get_top_opportunities("expensive", limit=3,  hours=28)
        mid = get_top_opportunities("midvalue",  limit=10, hours=28)
        send_daily_recap(exp, mid)

    if mode == "expensive":
        wl = WATCHLIST_EXPENSIVE
        print(f"\nScansione {len(wl)} query expensive...")
        for e in wl:
            try: scan_query(e["query"], e["name"], "expensive")
            except Exception as ex: print(f"  Err: {ex}")
            time.sleep(1)
    else:
        wl = get_midvalue_watchlist(40)
        print(f"\nScansione {len(wl)} target midvalue...")
        for e in wl:
            try: scan_query(e["query"], e["name"], "midvalue", e.get("artist",""))
            except Exception as ex: print(f"  Err: {ex}")
            time.sleep(1)

    today   = get_today_stats()
    alltime = get_all_time_stats()
    print(f"\nFine | Trovate: {today['today_found']} | €{alltime['total_profit_eur']:.2f}")


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nInterrotto")
    except Exception as e:
        print(f"\nERRORE:\n{traceback.format_exc()}")
        try: send_error_alert(str(e)[:500])
        except Exception: pass
