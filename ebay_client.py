"""
eBay Finding API v4
- Nessuna categoria fissa (evita HTTP 500)
- Rileva ristampe moderne di album vecchi
- Se non puo determinare la versione -> restituisce info incomplete
"""
import time, re, requests, urllib.parse
from config import EBAY_APP_ID

FINDING_URL = "https://svcs.ebay.com/services/search/FindingService/v1"

REISSUE_KEYWORDS = [
    "reissue","re-issue","remaster","remastered","re-master",
    "180g reissue","180 gram reissue","anniversary edition",
    "back to black","music on vinyl","vinyl me please",
    "demon records","wax love","speakers corner",
    "lacquer cut from digital","from digital master",
]

def is_configured():
    return bool(EBAY_APP_ID)


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


def detect_reissue(title: str, original_year: int) -> tuple:
    """
    Rileva se un listing eBay e una ristampa moderna di un album vecchio.
    Ritorna (is_reissue: bool, reason: str)
    original_year: anno di uscita originale dell'album su Discogs
    """
    tl = title.lower()

    # Controlla keyword ristampa esplicite
    for kw in REISSUE_KEYWORDS:
        if kw in tl:
            return True, f"keyword '{kw}' nel titolo"

    # Estrai anno dal titolo eBay (es. "2014", "2019", "(2022)")
    years_found = re.findall(r'\b(19[6-9]\d|20[0-2]\d)\b', title)
    if years_found and original_year and original_year > 0:
        listing_year = max(int(y) for y in years_found)
        # Se l'anno nel titolo e > 5 anni dopo l'originale -> ristampa
        if listing_year > original_year + 5:
            return True, f"anno {listing_year} vs originale {original_year}"

    return False, ""


def search_ebay(keywords, site_id="101", max_results=8, max_price=None):
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
        "itemFilter(0).name":             "Condition",
        "itemFilter(0).value(0)":         "3000",
        "itemFilter(0).value(1)":         "4000",
        "itemFilter(0).value(2)":         "2500",
    }
    if max_price:
        params["itemFilter(1).name"]       = "MaxPrice"
        params["itemFilter(1).value"]      = str(int(max_price))
        params["itemFilter(1).paramName"]  = "Currency"
        params["itemFilter(1).paramValue"] = "EUR"
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
            print(f"    eBay err: {err}")
            return []
        items = resp.get("searchResult",[{}])[0].get("item",[])
        result = items if isinstance(items,list) else []
        print(f"    eBay sito {site_id}: {len(result)} risultati")
        return result
    except Exception as e:
        print(f"    eBay exc ({site_id}): {str(e)[:50]}")
        return []


def find_best_listing(artist, title, original_year=0, max_price=None):
    """
    Cerca su eBay IT e UK.
    Filtra ristampe di album vecchi (ma non nuovi album recenti).
    Ritorna dict con listing o None.
    Aggiunge flag 'uncertain' se non si puo verificare la versione.
    """
    query    = f"{artist} {title} vinile vinyl lp"
    best     = None
    best_tot = float("inf")
    skipped_reissues = 0

    for site_id, site_name in [("101","eBay IT"),("3","eBay UK")]:
        items = search_ebay(query, site_id=site_id,
                            max_results=8, max_price=max_price)
        for item in items:
            try:
                price, ship, total = _price(item)
                if total <= 0 or total >= best_tot: continue
                eb_title = _val(item,"title","")
                tl = eb_title.lower()

                # Verifica che sia un vinile
                if not any(w in tl for w in ["vinyl","vinile"," lp","33 rpm","12\""]):
                    continue

                # Rileva ristampa (solo per album originali vecchi)
                # Se original_year > 2018 = album recente -> non filtrare
                is_reissue = False
                reissue_reason = ""
                if original_year > 0 and original_year <= 2018:
                    is_reissue, reissue_reason = detect_reissue(eb_title, original_year)

                if is_reissue:
                    print(f"    Skip ristampa: {eb_title[:50]} ({reissue_reason})")
                    skipped_reissues += 1
                    continue

                best_tot = total
                s = item.get("sellerInfo",[{}])[0]
                best = {
                    "price":     round(price,2),
                    "shipping":  round(ship,2),
                    "total":     total,
                    "url":       _val(item,"viewItemURL"),
                    "title":     eb_title,
                    "site":      site_name,
                    "condition": _val(item.get("condition",[{}])[0],
                                     "conditionDisplayName","Used"),
                    "seller":    _val(s,"sellerUserName",""),
                    # uncertain = non si puo verificare la versione con certezza
                    "uncertain": len(years_re := re.findall(
                        r'\b(19[6-9]\d|20[0-2]\d)\b', eb_title)) == 0,
                }
            except Exception: continue

    if best:
        status = "INCERTO" if best.get("uncertain") else "OK"
        print(f"    eBay best [{status}]: {best['site']} "
              f"€{best['total']:.0f} — {best['title'][:45]}")
    elif skipped_reissues:
        print(f"    Tutti {skipped_reissues} listing eBay erano ristampe")

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
