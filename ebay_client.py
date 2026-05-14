"""
eBay Finding API — cerca vinili su eBay IT e UK.
Richiede EBAY_APP_ID nei GitHub Secrets.
"""
import time, requests, urllib.parse
from config import EBAY_APP_ID

FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"


def is_configured():
    return bool(EBAY_APP_ID)


def _val(obj, key, default=""):
    """Estrae valore da lista o dict eBay (formato inconsistente)."""
    try:
        v = obj.get(key, [default])
        return v[0] if isinstance(v, list) else v
    except Exception:
        return default


def _price(item):
    """Estrae prezzo totale (listing + spedizione) da item eBay."""
    try:
        sell   = item.get("sellingStatus", [{}])[0]
        price  = float(_val(sell.get("convertedCurrentPrice", [{}])[0], "__value__", 0))
        ship_d = item.get("shippingInfo", [{}])[0]
        costs  = ship_d.get("shippingServiceCost", [{}])
        ship   = float(_val(costs[0] if costs else {}, "__value__", 0))
        return price, ship, price + ship
    except Exception:
        return 0.0, 0.0, 0.0


def search_ebay(artist, title, site_id="101", max_results=5, max_price=None):
    """
    Cerca su eBay per artista + titolo.
    site_id: 101=IT, 3=UK, 77=DE, 0=US
    """
    if not EBAY_APP_ID:
        return []

    query = f"{artist} {title} vinyl"
    params = {
        "OPERATION-NAME":                  "findItemsByKeywords",
        "SERVICE-VERSION":                 "1.0.0",
        "SECURITY-APPNAME":                EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT":            "JSON",
        "keywords":                        query,
        "categoryId":                      "306",
        "sortOrder":                       "PricePlusShippingLowest",
        "paginationInput.entriesPerPage":  str(max_results),
        "itemFilter(0).name":              "ListingType",
        "itemFilter(0).value":             "FixedPrice",
        "itemFilter(1).name":              "Condition",
        "itemFilter(1).value(0)":          "3000",
        "itemFilter(1).value(1)":          "4000",
        "itemFilter(1).value(2)":          "2500",
        "outputSelector(0)":               "SellerInfo",
        "siteid":                          site_id,
    }
    if max_price:
        params["itemFilter(2).name"]       = "MaxPrice"
        params["itemFilter(2).value"]      = str(max_price)
        params["itemFilter(2).paramName"]  = "Currency"
        params["itemFilter(2).paramValue"] = "EUR"

    try:
        r = requests.get(FINDING_URL, params=params, timeout=15)
        time.sleep(0.5)
        if r.status_code != 200:
            return []
        data = r.json()
        items = (data
                 .get("findItemsByKeywordsResponse", [{}])[0]
                 .get("searchResult", [{}])[0]
                 .get("item", []))
        return items if isinstance(items, list) else []
    except Exception as e:
        print(f"    eBay error: {e}")
        return []


def find_best_ebay_listing(artist, title, max_price=None):
    """
    Cerca su eBay IT e UK, ritorna il listing piu economico.
    Ritorna dict o None.
    """
    best = None
    best_total = float("inf")

    for site_id, site_name in [("101", "eBay IT"), ("3", "eBay UK")]:
        items = search_ebay(artist, title, site_id=site_id,
                            max_results=5, max_price=max_price)
        for item in items:
            try:
                price, ship, total = _price(item)
                if total <= 0:
                    continue
                if total < best_total:
                    best_total = total
                    best = {
                        "price":      round(price, 2),
                        "shipping":   round(ship, 2),
                        "total":      round(total, 2),
                        "url":        _val(item, "viewItemURL"),
                        "title":      _val(item, "title"),
                        "site":       site_name,
                        "condition":  _val(
                            item.get("condition", [{}])[0],
                            "conditionDisplayName", "Used"
                        ),
                        "seller":     _val(
                            item.get("sellerInfo", [{}])[0],
                            "sellerUserName", ""
                        ),
                        "item_id":    _val(item, "itemId"),
                    }
            except Exception:
                continue

    return best


def build_search_urls(artist, title):
    """Genera URL di ricerca per tutti i marketplace."""
    q = urllib.parse.quote_plus(f"{artist} {title} vinyl")
    return {
        "ebay_it":   f"https://www.ebay.it/sch/i.html?_nkw={q}&_sacat=306&LH_ItemCondition=3000&_sop=15",
        "ebay_uk":   f"https://www.ebay.co.uk/sch/i.html?_nkw={q}&_sacat=306&LH_ItemCondition=3000&_sop=15",
        "vinted":    f"https://www.vinted.it/catalog?search_text={urllib.parse.quote_plus(f'{artist} {title}')}",
        "wallapop":  f"https://it.wallapop.com/app/search?keywords={urllib.parse.quote_plus(f'{artist} {title}')}",
        "subito":    f"https://www.subito.it/annunci-italia/vendita/usato/?q={urllib.parse.quote_plus(f'{artist} {title}')}",
    }
