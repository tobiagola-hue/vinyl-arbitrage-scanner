"""
VINYL ARBITRAGE SCANNER v14
- eBay senza categoria (fix HTTP 500)
- Watchlist dinamica e rotante
- Soglie minime per trovare qualcosa
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
from watchlist import WATCHLIST_EXPENSIVE, get_midvalue_watchlist
from config import (
    MIN_SCORE, MIN_PROFIT_EUR, MIN_ROI,
    MAX_RATIO_EXPENSIVE, MIN_MEDIAN_EXPENSIVE, MIN_WANT_EXPENSIVE,
    MAX_RATIO_MIDVALUE, MIN_MEDIAN_MIDVALUE, MIN_WANT_MIDVALUE,
)

MAX_DISC_RESULTS = 5


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
        if a: return a[0].get("name", "?")
        t = d.get("title", "?")
        return t.split(" - ")[0].strip() if " - " in t else "?"
    except Exception: return "?"


def get_label(d):
    try:
        l = d.get("labels") or []
        return l[0].get("name", "") if l else ""
    except Exception: return ""


def get_vgplus_median(release_id):
    sugg = dc.get_price_suggestions(release_id)
    if not sugg: return 0.0
    for cond in ("Very Good Plus (VG+)", "Near Mint (NM or M-)", "Mint (M)"):
        v = sg(sugg, cond, "value")
        if v and float(v) > 0:
            mult = 1.0 if "Near Mint" in cond else 0.75 if "Mint" in cond else 1.0
            return round(float(v) * mult, 2)
    return 0.0


def get_ref_price(det):
    """Prezzo riferimento: usa lowest_price*1.5 come stima mediana."""
    try:
        lp = float(det.get("lowest_price") or 0)
        if lp > 0: return round(lp * 1.5, 2)
    except Exception: pass
    return 0.0


def get_cheapest_vgplus(release_id):
    listings = dc.get_marketplace_listings(release_id)
    if not listings: return None
    best = None
    best_price = float("inf")
    for lst in listings:
        cond = lst.get("condition", "") or ""
        if cond not in ["Mint (M)", "Near Mint (NM or M-)", "Very Good Plus (VG+)"]:
            continue
        p = lst.get("price") or 0
        price = float(p.get("value", 0) if isinstance(p, dict) else p or 0)
        if price <= 0 or price >= best_price: continue
        best_price = price
        s = lst.get("seller") or {}
        best = {
            "price": price, "condition": cond,
            "listing_id": str(lst.get("id", "") or ""),
            "seller": s.get("username", "vedi link") or "vedi link",
            "rating": float(sg(s, "stats", "rating") or 100),
            "reviews": int(sg(s, "stats", "total") or 0),
            "ships_from": lst.get("ships_from", "EU") or "EU",
        }
    return best


def build_opp(opp_id, mode, release_id, artist, title, label, year,
              country, condition, buy_price, ref_price, pdata,
              rsigs, flags, want, sale, seller, rating, reviews,
              buy_url, release_url, buy_site):
    opp = {
        "listing_id": opp_id, "source": buy_site.lower(), "mode": mode,
        "release_id": str(release_id), "artist": artist, "title": title,
        "label": label, "year": year, "country": country,
        "condition": condition, "listing_price": buy_price,
        "median_price": ref_price,
        "est_sell_price": pdata.get("est_sell_price", 0),
        "gross_profit": pdata.get("gross_profit", 0),
        "roi": pdata.get("roi", 0),
        "rarity_signals": rsigs, "red_flags": flags,
        "wantlist_count": want, "num_for_sale": sale,
        "seller_username": seller, "seller_rating": rating,
        "seller_reviews": reviews,
        "listing_url": buy_url, "release_url": release_url,
        "buy_site": buy_site,
    }
    try: opp["score"] = score_opportunity(opp)
    except Exception: opp["score"] = 5.0
    return opp


def alert_if_good(opp):
    save_opportunity(opp)
    print(f"    {'TROVATO':8} {opp['artist']} — {opp['title']} | "
          f"€{opp['listing_price']:.0f} vs €{opp['median_price']:.0f} | "
          f"ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10")
    if opp["score"] >= MIN_SCORE:
        try:
            if send_opportunity_alert(opp):
                mark_alerted(opp["listing_id"])
                print(f"    ALERT INVIATO")
                time.sleep(2)
        except Exception as e:
            print(f"    Telegram: {e}")
        return 1
    return 0


# ─── EXPENSIVE ─────────────────────────────────────────────────

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

        if want < MIN_WANT_EXPENSIVE: print(f"      Skip want={want}"); return 0
        if sale < 1: print(f"      Skip nessuno in vendita"); return 0

        median = get_vgplus_median(release_id)
        if median < MIN_MEDIAN_EXPENSIVE:
            print(f"      Skip mediana €{median:.0f}"); return 0

        listing = get_cheapest_vgplus(release_id)
        if not listing: print(f"      Skip nessun VG+"); return 0

        ratio = listing["price"] / median if median > 0 else 1.0
        print(f"      want={want} | VG+ €{listing['price']:.0f}/€{median:.0f} | {ratio:.0%}")

        if ratio > MAX_RATIO_EXPENSIVE:
            print(f"      Skip ratio {ratio:.0%}"); return 0

        opp_id = f"exp_{release_id}_{date.today().isoformat()}"
        if opportunity_exists(opp_id): return 0

        lid = listing["listing_id"]
        buy_url = (f"https://www.discogs.com/sell/item/{lid}"
                   if lid else dc.get_marketplace_url(release_id))
        text  = f"{artist} {title} {label} {notes}".lower()
        rsigs = find_rarity_signals(text); flags = find_red_flags(text)
        try:
            if detect_first_press_from_matrix(notes): rsigs.append("first press")
            for e in detect_engineer_initials(notes): rsigs.append(f"engineer: {e}")
        except Exception: pass

        try: pdata = calc_profit(listing["price"], median, listing["condition"], listing["ships_from"])
        except Exception: return 0

        if pdata.get("gross_profit",0) < MIN_PROFIT_EUR:
            print(f"      Skip profitto €{pdata.get('gross_profit',0):.0f}"); return 0
        if pdata.get("roi",0) < MIN_ROI:
            print(f"      Skip ROI {pdata.get('roi',0)*100:.0f}%"); return 0

        opp = build_opp(opp_id,"expensive",release_id,artist,title,label,year,
                        country,listing["condition"],listing["price"],median,pdata,
                        rsigs,flags,want,sale,listing["seller"],
                        listing["rating"],listing["reviews"],
                        buy_url,dc.get_release_url(release_id),"Discogs")
        return alert_if_good(opp)
    except Exception as e:
        print(f"    Errore {release_id}: {e}"); return 0


# ─── MIDVALUE ──────────────────────────────────────────────────

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

        if want < MIN_WANT_MIDVALUE:
            print(f"      Skip want={want}"); return 0

        ref = get_ref_price(det)
        lp  = float(det.get("lowest_price") or 0)
        if ref < MIN_MEDIAN_MIDVALUE:
            print(f"      Skip ref €{ref:.0f} (lowest=€{lp:.0f})"); return 0

        print(f"  -> {artist} — {title} | lowest=€{lp:.0f} ref=€{ref:.0f} want={want}")

        search_artist = artist if artist != "?" else artist_hint
        max_ebay = ref * MAX_RATIO_MIDVALUE
        ebay = ec.find_best_listing(search_artist, title, max_price=max_ebay)

        if not ebay:
            print(f"      Nessun eBay sotto €{max_ebay:.0f}"); return 0

        ratio = ebay["total"] / ref if ref > 0 else 1.0
        if ratio > MAX_RATIO_MIDVALUE:
            print(f"      Skip ratio {ratio:.0%}"); return 0

        opp_id = f"mid_{rid}_{date.today().isoformat()}"
        if opportunity_exists(opp_id): return 0

        try: pdata = calc_profit(ebay["total"], ref, "Very Good (VG)", country)
        except Exception: return 0

        if pdata.get("gross_profit",0) < MIN_PROFIT_EUR:
            print(f"      Skip profitto €{pdata.get('gross_profit',0):.0f}"); return 0
        if pdata.get("roi",0) < MIN_ROI:
            print(f"      Skip ROI {pdata.get('roi',0)*100:.0f}%"); return 0

        text  = f"{artist} {title} {label} {notes}".lower()
        rsigs = find_rarity_signals(text); flags = find_red_flags(text)

        opp = build_opp(opp_id,"midvalue",rid,artist,title,label,year,
                        country,f"Used ({ebay['condition']})",
                        ebay["total"],ref,pdata,rsigs,flags,want,0,
                        ebay.get("seller",""),0,0,
                        ebay.get("url",""),dc.get_release_url(rid),
                        ebay.get("site","eBay"))
        return alert_if_good(opp)
    except Exception as e:
        print(f"    Errore release {rid}: {e}"); return 0


def scan_query(query, name, mode, artist_hint=""):
    print(f"\n  [{name}]")
    try: res = dc.search_releases(query=query)
    except Exception as e: print(f"    Search err: {e}"); return 0
    if not res: return 0
    releases = (res.get("results") or [])[:MAX_DISC_RESULTS]
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
    mode  = get_mode()
    h     = italy_hour()
    recap = check_recap()

    print("="*55)
    print(f"VINYL ARBITRAGE v14 | Ora IT: {h}:xx | {mode.upper()}")
    if mode == "midvalue":
        print(f"eBay: {'ON' if ec.is_configured() else 'OFF'}")
    print("="*55)

    init_db()
    send_startup_message(mode)

    if recap == "expensive":
        send_recap_expensive(get_top_opportunities("expensive",3,1))
    elif recap == "midvalue_1300":
        send_recap_midvalue(get_top_opportunities("midvalue",10,1),"13:00")
    elif recap == "midvalue_1800":
        send_recap_midvalue(get_top_opportunities("midvalue",10,1),"18:00")

    if mode == "expensive":
        wl = WATCHLIST_EXPENSIVE
        print(f"\nScansione {len(wl)} query Discogs...")
        for e in wl:
            try: scan_query(e["query"], e["name"], "expensive")
            except Exception as ex: print(f"  Err: {ex}")
            time.sleep(1)
    else:
        wl = get_midvalue_watchlist(40)
        print(f"\nScansione {len(wl)} target eBay+Discogs (dinamici)...")
        for e in wl:
            try: scan_query(e["query"], e["name"], "midvalue", e.get("artist",""))
            except Exception as ex: print(f"  Err: {ex}")
            time.sleep(1)

    today   = get_today_stats()
    alltime = get_all_time_stats()
    print(f"\nFine | Trovate: {today['today_found']} | Alert: {today['today_alerted']}")
    send_daily_summary({
        "scanned": len(wl)*MAX_DISC_RESULTS,
        "today_found": today["today_found"],
        "today_alerted": today["today_alerted"],
        **alltime,
    })


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nInterrotto")
    except Exception as e:
        print(f"\nERRORE:\n{traceback.format_exc()}")
        try: send_error_alert(str(e)[:500])
        except Exception: pass
