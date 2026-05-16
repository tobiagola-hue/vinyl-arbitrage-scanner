"""
eBay Finding API — cerca vinili su eBay IT e UK.
Richiede EBAY_APP_ID nei GitHub Secrets.
"""
import time, requests, urllib.parse
from config import EBAY_APP_ID

FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"

# Categorie eBay per Records/Vinyl per sito
# sito IT=101: 176975 (Vinili), sito UK=3: 306 (Records)
CATEGORIES = {
    "101": "176975",  # eBay Italia - Musica > Vinili
    "3":   "306",     # eBay UK - Music > Records
    "77":  "11325",   # eBay Germania - Musik > Vinyl-Schallplatten
}


def is_configured():
    return bool(EBAY_APP_ID)


def _val(obj, key, default=""):
    try:
        v = obj.get(key, [default])
        return v[0] if isinstance(v, list) else v
    except Exception:
        return default


def _price(item):
    try:
        sell  = item.get("sellingStatus", [{}])[0]
        price = float(_val(sell.get("convertedCurrentPrice", [{}])[0], "__value__", 0))
        ship_d = item.get("shippingInfo", [{}])[0]
        costs  = ship_d.get("shippingServiceCost", [])
        ship   = float(_val(costs[0] if costs else {}, "__value__", 0))
        return price, ship, round(price + ship, 2)
    except Exception:
        return 0.0, 0.0, 0.0


def search_ebay(artist, title, site_id="101", max_results=8, max_price=None):
    if not EBAY_APP_ID:
        return []

    query    = f"{artist} {title} vinyl"
    cat_id   = CATEGORIES.get(site_id, "")

    params = {
        "OPERATION-NAME":                 "findItemsByKeywords",
        "SERVICE-VERSION":                "1.0.0",
        "SECURITY-APPNAME":               EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT":           "JSON",
        "keywords":                       query,
        "sortOrder":                      "PricePlusShippingLowest",
        "paginationInput.entriesPerPage": str(max_results),
        "outputSelector(0)":              "SellerInfo",
        "siteid":                         site_id,
    }

    if cat_id:
        params["categoryId"] = cat_id

    # Filtro condizione: usato (3000) e very good (4000)
    params["itemFilter(0).name"]     = "Condition"
    params["itemFilter(0).value(0)"] = "3000"
    params["itemFilter(0).value(1)"] = "4000"
    params["itemFilter(0).value(2)"] = "2500"

    if max_price:
        params["itemFilter(1).name"]       = "MaxPrice"
        params["itemFilter(1).value"]      = str(int(max_price))
        params["itemFilter(1).paramName"]  = "Currency"
        params["itemFilter(1).paramValue"] = "EUR"

    try:
        r = requests.get(FINDING_URL, params=params, timeout=15)
        time.sleep(0.5)
        if r.status_code != 200:
            print(f"    eBay HTTP {r.status_code} su sito {site_id}")
            return []
        data  = r.json()
        resp  = data.get("findItemsByKeywordsResponse", [{}])[0]
        ack   = _val(resp, "ack", "Failure")
        if ack != "Success":
            err = resp.get("errorMessage", [{}])[0].get("error", [{}])[0].get("message", ["?"])[0]
            print(f"    eBay errore ({site_id}): {err}")
            return []
        items = resp.get("searchResult", [{}])[0].get("item", [])
        result = items if isinstance(items, list) else []
        print(f"    eBay sito {site_id}: {len(result)} risultati per '{query}'")
        return result
    except Exception as e:
        print(f"    eBay exception ({site_id}): {e}")
        return []


def find_best_ebay_listing(artist, title, max_price=None):
    """Cerca su eBay IT e UK, ritorna il listing piu economico o None."""
    best       = None
    best_total = float("inf")

    for site_id, site_name in [("101", "eBay IT"), ("3", "eBay UK")]:
        items = search_ebay(artist, title, site_id=site_id,
                            max_results=8, max_price=max_price)
        for item in items:
            try:
                price, ship, total = _price(item)
                if total <= 0 or total >= best_total:
                    continue
                title_ebay = _val(item, "title", "")
                # Verifica che sia un vinile (contiene LP, vinyl, vinile, ecc.)
                tl = title_ebay.lower()
                if not any(w in tl for w in ["vinyl","vinile","lp","33 rpm","12\""]):
                    continue
                best_total = total
                best = {
                    "price":     round(price, 2),
                    "shipping":  round(ship, 2),
                    "total":     total,
                    "url":       _val(item, "viewItemURL"),
                    "title":     title_ebay,
                    "site":      site_name,
                    "condition": _val(item.get("condition",[{}])[0], "conditionDisplayName","Used"),
                    "seller":    _val(item.get("sellerInfo",[{}])[0], "sellerUserName",""),
                    "item_id":   _val(item, "itemId"),
                }
            except Exception:
                continue

    if best:
        print(f"    Miglior listing: {best['site']} €{best['total']:.0f} — {best['title'][:50]}")
    return best


def build_search_urls(artist, title):
    q  = urllib.parse.quote_plus(f"{artist} {title} vinyl")
    q2 = urllib.parse.quote_plus(f"{artist} {title}")
    return {
        "ebay_it":  f"https://www.ebay.it/sch/i.html?_nkw={q}&_sacat=176975&_sop=15",
        "ebay_uk":  f"https://www.ebay.co.uk/sch/i.html?_nkw={q}&_sacat=306&_sop=15",
        "vinted":   f"https://www.vinted.it/catalog?search_text={q2}",
        "wallapop": f"https://it.wallapop.com/app/search?keywords={q2}",
        "subito":   f"https://www.subito.it/annunci-italia/vendita/usato/?q={q2}",
    }
