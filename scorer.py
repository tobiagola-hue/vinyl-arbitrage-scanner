import re
from config import (
    DISCOGS_FEE, SHIPPING_OUT, PACKAGING_COST,
    SHIPPING_IN_EU, SHIPPING_IN_US, SHIPPING_IN_JP,
    MIN_ROI, MIN_PROFIT_EUR, ACCEPTED_CONDITIONS,
)
from watchlist import RARITY_KEYWORDS, RED_FLAGS, COUNTRY_VALUE_MULTIPLIERS


def _f(v, d=0.0):
    try: return float(v or d)
    except Exception: return d


def _i(v, d=0):
    try: return int(v or d)
    except Exception: return d


def estimate_sell_price(median, condition, country="EU"):
    mults = {
        "Mint (M)":             1.15,
        "Near Mint (NM or M-)": 1.00,
        "Very Good Plus (VG+)": 0.90,
        "Very Good (VG)":       0.70,
    }
    mult = 0.85
    cl = (condition or "").lower()
    for k, v in mults.items():
        if k.lower() in cl:
            mult = v
            break
    cm = COUNTRY_VALUE_MULTIPLIERS.get(country, 1.0)
    return round(_f(median) * mult * cm, 2)


def calc_shipping_in(country):
    if country in ("Japan",): return SHIPPING_IN_JP
    if country in ("US","Canada"): return SHIPPING_IN_US
    return SHIPPING_IN_EU


def calc_profit(buy_price, median, condition, country="EU"):
    bp   = _f(buy_price)
    med  = _f(median)
    ship = calc_shipping_in(country or "EU")
    cost = bp + ship + PACKAGING_COST
    sell = estimate_sell_price(med, condition or "", country or "EU")
    fees = round(sell * DISCOGS_FEE, 2)
    net  = round(sell - fees - SHIPPING_OUT - cost, 2)
    roi  = round(net / cost, 4) if cost > 0 else 0.0
    return {
        "listing_price": bp, "shipping_in": ship,
        "total_cost": round(cost,2), "est_sell_price": sell,
        "platform_fees": fees, "gross_profit": net, "roi": roi,
    }


def find_rarity_signals(text):
    if not text: return []
    tl = text.lower()
    return [kw for kw in RARITY_KEYWORDS if kw in tl]


def find_red_flags(text):
    if not text: return []
    tl = text.lower()
    return [rf for rf in RED_FLAGS if rf in tl]


def detect_first_press_from_matrix(notes):
    if not notes: return False
    return bool(re.search(r'\b(A[-\s]?1|1A|B[-\s]?1|1B)\b', notes, re.IGNORECASE))


def detect_engineer_initials(notes):
    if not notes: return []
    eng = {"RL":"Robert Ludwig","BG":"Bernie Grundman","PORKY":"George Peckham"}
    nu = notes.upper()
    return [f"{k} ({v})" for k,v in eng.items() if k in nu]


def score_opportunity(opp):
    score = 0.0
    roi    = _f(opp.get("roi"))
    profit = _f(opp.get("gross_profit"))
    wants  = _i(opp.get("wantlist_count"))
    sale   = _i(opp.get("num_for_sale"))
    rating = _f(opp.get("seller_rating"), 100)
    lp     = _f(opp.get("listing_price"))
    med    = _f(opp.get("median_price"), 1)
    cond   = (opp.get("condition") or "").lower()
    sigs   = opp.get("rarity_signals") or []
    flags  = opp.get("red_flags") or []

    if roi >= 1.50:      score += 3.0
    elif roi >= 1.00:    score += 2.5
    elif roi >= 0.75:    score += 2.0
    elif roi >= 0.50:    score += 1.5
    elif roi >= MIN_ROI: score += 1.0
    else:                score -= 1.0

    if profit >= 80:     score += 1.5
    elif profit >= 50:   score += 1.0
    elif profit >= 25:   score += 0.5
    elif profit < MIN_PROFIT_EUR: score -= 0.5

    if "mint (m)" == cond:         score += 1.5
    elif "near mint" in cond:      score += 1.2
    elif "very good plus" in cond: score += 0.7

    if wants >= 2000:    score += 1.5
    elif wants >= 1000:  score += 1.0
    elif wants >= 500:   score += 0.7
    elif wants >= 200:   score += 0.3
    elif wants >= 50:    score += 0.1

    if 1 <= sale <= 5:   score += 0.5
    elif sale <= 20:     score += 0.2
    elif sale >= 100:    score -= 0.3

    score += min(len(sigs) * 0.4, 2.0)
    score -= len(flags) * 0.5

    if rating < 97:      score -= 1.0

    ratio = lp / med if med > 0 else 1
    if ratio <= 0.30:    score += 0.5
    elif ratio <= 0.45:  score += 0.3

    return round(max(1.0, min(10.0, score)), 1)

