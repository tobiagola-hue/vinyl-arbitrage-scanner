"""eBay Finding API v5 — senza filtro condizione (fix HTTP 500), UK prima di IT."""
import time, re, requests, urllib.parse
from config import EBAY_APP_ID

FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
REISSUE_KEYWORDS = [
    "reissue","re-issue","remaster","remastered","180g reissue",
    "anniversary edition","back to black","music on vinyl",
    "demon records","wax love","speakers corner","lacquer cut from digital",
]

def is_configured(): return bool(EBAY_APP_ID)

def _val(obj, key, default=""):
    try:
        v = obj.get(key, [default])
        return v[0] if isinstance(v, list) else v
    except Exception: return default

def _price(item):
    try:
        sell  = item.get("sellingStatus",[{}])[0]
        price = float(_val(sell.get("convertedCurrentPrice",[{}])[0],"__value__",0))
        ships = item.get("shippingInfo",[{}])[0].get("shippingServiceCost",[])
        ship  = float(_val(ships[0] if ships else {},"__value__",0))
        return price, ship, round(price+ship, 2)
    except Exception: return 0.0, 0.0, 0.0

def detect_reissue(title, original_year):
    tl = title.lower()
    for kw in REISSUE_KEYWORDS:
        if kw in tl: return True, f"keyword '{kw}'"
    years = re.findall(r'\b(19[6-9]\d|20[0-2]\d)\b', title)
    if years and original_year and original_year > 0:
        ly = max(int(y) for y in years)
        if ly > original_year + 5:
            return True, f"anno {ly} vs originale {original_year}"
    return False, ""

def search_ebay(keywords, site_id="3", max_results=8, max_price=None):
    if not EBAY_APP_ID: return []
    params = {
        "OPERATION-NAME":                 "findItemsByKeywords",
        "SERVICE-VERSION":                "1.0.0",
        "SECURITY-APPNAME":               EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT":           "JSON",
        "keywords":                       keywords,
        "sortOrder":                      "PricePlusShippingLowest",
        "paginationInput.entriesPerPage": str(max_results),
        "outputSelector(0)":              "SellerInfo",
        "siteid":                         site_id,
    }
    if max_price:
        params["itemFilter(0).name"]       = "MaxPrice"
        params["itemFilter(0).value"]      = str(int(max_price))
        params["itemFilter(0).paramName"]  = "Currency"
        params["itemFilter(0).paramValue"] = "EUR"
    try:
        r = requests.get(FINDING_URL, params=params, timeout=12)
        time.sleep(0.3)
        if r.status_code != 200:
            print(f"    eBay HTTP {r.status_code} (sito {site_id})")
            return []
        data = r.json()
        resp = data.get("findItemsByKeywordsResponse",[{}])[0]
        if _val(resp,"ack","Failure") != "Success":
            err = (resp.get("errorMessage",[{}])[0]
                   .get("error",[{}])[0].get("message",["?"])[0])
            print(f"    eBay err ({site_id}): {err}")
            return []
        items = resp.get("searchResult",[{}])[0].get("item",[])
        result = items if isinstance(items,list) else []
        print(f"    eBay sito {site_id}: {len(result)} risultati")
        return result
    except Exception as e:
        print(f"    eBay exc ({site_id}): {str(e)[:50]}")
        return []

def find_best_listing(artist, title, original_year=0, max_price=None):
    query = f"{artist} {title} vinyl lp"
    best = None; best_tot = float("inf")
    for site_id, site_name in [("3","eBay UK"),("101","eBay IT")]:
        items = search_ebay(query, site_id=site_id, max_results=8, max_price=max_price)
        for item in items:
            try:
                price, ship, total = _price(item)
                if total <= 0 or total >= best_tot: continue
                eb_title = _val(item,"title","")
                tl = eb_title.lower()
                if not any(w in tl for w in ["vinyl","vinile"," lp","33 rpm","12\"","record"]):
                    continue
                if original_year > 0 and original_year <= 2018:
                    is_rei, reason = detect_reissue(eb_title, original_year)
                    if is_rei:
                        print(f"    Skip ristampa: {eb_title[:40]} ({reason})")
                        continue
                best_tot = total
                s = item.get("sellerInfo",[{}])[0]
                years_in = re.findall(r'\b(19[6-9]\d|20[0-2]\d)\b', eb_title)
                best = {
                    "price": round(price,2), "shipping": round(ship,2), "total": total,
                    "url": _val(item,"viewItemURL"), "title": eb_title, "site": site_name,
                    "condition": _val(item.get("condition",[{}])[0],"conditionDisplayName","Used"),
                    "seller": _val(s,"sellerUserName",""),
                    "uncertain": len(years_in) == 0,
                }
            except Exception: continue
    if best:
        unc = " [INCERTO]" if best.get("uncertain") else ""
        print(f"    eBay best{unc}: {best['site']} €{best['total']:.0f} — {best['title'][:45]}")
    return best

def build_search_urls(artist, title):
    q  = urllib.parse.quote_plus(f"{artist} {title} vinyl")
    q2 = urllib.parse.quote_plus(f"{artist} {title}")
    return {
        "ebay_it":  f"https://www.ebay.it/sch/i.html?_nkw={q}&_sop=15",
        "ebay_uk":  f"https://www.ebay.co.uk/sch/i.html?_nkw={q}&_sop=15",
        "vinted":   f"https://www.vinted.it/catalog?search_text={q2}",
        "wallapop": f"https://it.wallapop.com/app/search?keywords={q2}",
        "subito":   f"https://www.subito.it/annunci-italia/vendita/usato/?q={q2}",
    }
