“””
VINYL ARBITRAGE SCANNER — scanner.py v8
Link diretto al listing più economico su Discogs (con OAuth).
Prezzi reali da price_suggestions OAuth.
“””
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
MIN_PROFIT_EUR, MIN_ROI
)

MAX_RESULTS_PER_QUERY = 8
MIN_WANTLIST          = 20
FALLBACK_MEDIAN_MULT  = 1.8

def safe_get(d, *keys, default=None):
for k in keys:
if not isinstance(d, dict):
return default
d = d.get(k, default)
return d

def get_artist_name(details: dict) -> str:
try:
artists = details.get(“artists”) or []
if artists:
return artists[0].get(“name”, “?”)
t = details.get(“title”, “?”)
return t.split(” - “)[0].strip() if “ - “ in t else “?”
except Exception:
return “?”

def get_label_name(details: dict) -> str:
try:
labels = details.get(“labels”) or []
return labels[0].get(“name”, “”) if labels else “”
except Exception:
return “”

def get_median(release_id: int, lowest: float) -> tuple:
“”“Ritorna (mediana_reale, condizione) usando OAuth price_suggestions.”””
suggestions = dc.get_price_suggestions(release_id)
if suggestions and isinstance(suggestions, dict):
for cond in (“Near Mint (NM or M-)”, “Very Good Plus (VG+)”, “Mint (M)”, “Very Good (VG)”):
try:
val = safe_get(suggestions, cond, “value”)
if val and float(val) > 0:
return float(val), cond
except Exception:
continue
# Fallback stima
if lowest and float(lowest) > 0:
return round(float(lowest) * FALLBACK_MEDIAN_MULT, 2), “Very Good Plus (VG+)”
return 0.0, “”

def get_best_listing(release_id: int) -> dict:
“””
Recupera il listing più economico via OAuth.
Ritorna dict con: price, condition, listing_id, seller, ships_from
“””
result = {
“price”:      0.0,
“condition”:  “”,
“listing_id”: “”,
“seller”:     “vedi link”,
“rating”:     100.0,
“reviews”:    0,
“ships_from”: “EU”,
}
try:
listings = dc.get_marketplace_listings(release_id)
if not listings:
return result
first = listings[0]
p = first.get(“price”) or 0
result[“price”]      = float(p.get(“value”, 0) if isinstance(p, dict) else p or 0)
result[“condition”]  = first.get(“condition”, “”) or “”
result[“listing_id”] = str(first.get(“id”, “”) or “”)
s = first.get(“seller”) or {}
result[“seller”]     = s.get(“username”, “vedi link”) or “vedi link”
result[“rating”]     = float(safe_get(s, “stats”, “rating”) or 100)
result[“reviews”]    = int(safe_get(s, “stats”, “total”) or 0)
result[“ships_from”] = first.get(“ships_from”, “EU”) or “EU”
except Exception:
pass
return result

def analyze_release(release_id: int) -> int:
try:
details = dc.get_release_details(release_id)
if not details:
return 0

```
    artist   = get_artist_name(details)
    title    = details.get("title", "?") or "?"
    label    = get_label_name(details)
    year     = str(details.get("year", "") or "")
    country  = details.get("country", "EU") or "EU"
    notes    = details.get("notes", "") or ""

    try: wantlist = int(safe_get(details, "community", "want", default=0) or 0)
    except Exception: wantlist = 0

    try: for_sale = int(details.get("num_for_sale", 0) or 0)
    except Exception: for_sale = 0

    try: lowest = float(details.get("lowest_price", 0) or 0)
    except Exception: lowest = 0.0

    if wantlist < MIN_WANTLIST:
        print(f"      ↳ Skip: want={wantlist} < {MIN_WANTLIST}")
        return 0
    if for_sale < 1:
        print(f"      ↳ Skip: nessuno in vendita")
        return 0
    if lowest <= 0:
        print(f"      ↳ Skip: prezzo non disponibile")
        return 0

    median, ref_cond = get_median(release_id, lowest)
    if median <= 0 or median < MIN_MEDIAN_EUR:
        print(f"      ↳ Skip: mediana €{median:.0f} sotto soglia")
        return 0

    ratio = lowest / median if median > 0 else 1.0
    print(f"      ↳ want={wantlist} | lowest=€{lowest:.0f} | mediana=€{median:.0f} | ratio={ratio:.0%} | in vendita={for_sale}")

    if ratio > MAX_PRICE_RATIO:
        print(f"      ↳ Skip: ratio {ratio:.0%} > {MAX_PRICE_RATIO:.0%}")
        return 0

    opp_id = f"release_{release_id}"
    if opportunity_exists(opp_id):
        return 0

    # ── Recupera listing reale con OAuth ─────────────
    listing = get_best_listing(release_id)

    # Usa prezzo reale del listing se disponibile, altrimenti lowest
    buy_price   = listing["price"] if listing["price"] > 0 else lowest
    condition   = listing["condition"] if listing["condition"] else ref_cond
    listing_id  = listing["listing_id"]
    ships_from  = listing["ships_from"]

    # ── Link: diretto al listing più economico ────────
    if listing_id:
        # Link diretto alla pagina del listing specifico (con "Aggiungi al carrello")
        buy_url = f"https://www.discogs.com/sell/item/{listing_id}"
    else:
        # Fallback: lista marketplace ordinata per prezzo
        buy_url = dc.get_marketplace_url(release_id)

    # Link scheda disco
    release_url = dc.get_release_url(release_id)

    # ── Analisi testo ─────────────────────────────────
    full_text   = f"{artist} {title} {label} {notes}".lower()
    rarity_sigs = find_rarity_signals(full_text)
    flags       = find_red_flags(full_text)
    try:
        if detect_first_press_from_matrix(notes):
            rarity_sigs.append("first press (matrix detected)")
        for eng in detect_engineer_initials(notes):
            rarity_sigs.append(f"engineer: {eng}")
    except Exception:
        pass

    # ── Calcolo profitto ──────────────────────────────
    try:
        profit_data = calc_profit(buy_price, median, condition, ships_from)
    except Exception:
        return 0

    if profit_data.get("gross_profit", 0) < MIN_PROFIT_EUR:
        print(f"      ↳ Skip: profitto €{profit_data.get('gross_profit',0):.0f} < €{MIN_PROFIT_EUR}")
        return 0
    if profit_data.get("roi", 0) < MIN_ROI:
        print(f"      ↳ Skip: ROI {profit_data.get('roi',0)*100:.0f}% < {MIN_ROI*100:.0f}%")
        return 0

    opp = {
        "listing_id":      opp_id,
        "source":          "discogs",
        "release_id":      str(release_id),
        "artist":          artist,
        "title":           title,
        "label":           label,
        "year":            year,
        "country":         country,
        "condition":       condition,
        "listing_price":   buy_price,
        "median_price":    median,
        "est_sell_price":  profit_data.get("est_sell_price", 0),
        "gross_profit":    profit_data.get("gross_profit", 0),
        "roi":             profit_data.get("roi", 0),
        "rarity_signals":  rarity_sigs,
        "red_flags":       flags,
        "wantlist_count":  wantlist,
        "num_for_sale":    for_sale,
        "seller_username": listing["seller"],
        "seller_rating":   listing["rating"],
        "seller_reviews":  listing["reviews"],
        "listing_url":     buy_url,        # Link diretto al listing più economico
        "notes":           release_url,    # Link scheda disco (salvato in notes)
    }

    try:
        opp["score"] = score_opportunity(opp)
    except Exception:
        opp["score"] = 5.0

    save_opportunity(opp)

    print(
        f"    💎 {artist} — {title} | "
        f"€{buy_price:.0f} vs €{median:.0f} | "
        f"ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10"
    )

    if opp["score"] >= MIN_SCORE:
        # Passa anche il release_url per il secondo link
        opp["release_url"] = release_url
        try:
            if send_opportunity_alert(opp):
                mark_alerted(opp_id)
                print(f"    ✅ ALERT INVIATO — Score {opp['score']}/10")
                time.sleep(2)
        except Exception as e:
            print(f"    ⚠️ Telegram: {e}")
        return 1

    return 0

except Exception as e:
    print(f"    ⚠️ Errore release {release_id}: {e}")
    return 0
```

def scan_query(query: str, name: str, tier: str) -> int:
print(f”\n🔎 [{tier}] {name}”)
try:
results = dc.search_releases(query=query)
except Exception as e:
print(f”    Errore search: {e}”)
return 0

```
if not results:
    return 0

releases = (results.get("results") or [])[:MAX_RESULTS_PER_QUERY]
found = 0
for r in releases:
    try:
        rid = r.get("id")
        if not rid:
            continue
        print(f"  → {r.get('title','?')} [{rid}]")
        found += analyze_release(rid)
    except Exception as e:
        print(f"    ⚠️ {e}")
    time.sleep(0.8)
return found
```

def main():
mode = “OAuth 🔐” if dc.HAS_OAUTH else “Token ⚠️”
print(”=” * 55)
print(f”🎵 VINYL ARBITRAGE SCANNER v8 | {mode}”)
print(”=” * 55)

```
init_db()
send_startup_message()

for tier in ("A", "B", "C"):
    entries = [e for e in WATCHLIST if e.get("tier") == tier]
    print(f"\n{'='*20} TIER {tier} — {len(entries)} ricerche {'='*20}")
    for entry in entries:
        try:
            scan_query(entry.get("query",""), entry.get("name","?"), tier)
        except Exception as e:
            print(f"  ❌ {entry.get('name','?')}: {e}")
        time.sleep(1)

today   = get_today_stats()
alltime = get_all_time_stats()
print(f"\n✅ Fine | Trovate: {today['today_found']} | Alert: {today['today_alerted']}")
send_daily_summary({
    "scanned":       len(WATCHLIST) * MAX_RESULTS_PER_QUERY,
    "today_found":   today["today_found"],
    "today_alerted": today["today_alerted"],
    **alltime,
})
```

if **name** == “**main**”:
try:
main()
except KeyboardInterrupt:
print(”\n⛔ Interrotto”)
except Exception as e:
print(f”\n❌ ERRORE:\n{traceback.format_exc()}”)
try: send_error_alert(str(e)[:500])
except Exception: pass