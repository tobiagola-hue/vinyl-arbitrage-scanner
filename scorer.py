"""
VINYL ARBITRAGE SCANNER — Scorer v3
Gestisce tutti i casi edge (None, stringhe vuote, tipi errati).
"""
import re
from config import (
    DISCOGS_FEE, SHIPPING_OUT, PACKAGING_COST,
    SHIPPING_IN_EU, SHIPPING_IN_US, SHIPPING_IN_JP,
    MIN_ROI, MIN_PROFIT_EUR, MIN_MEDIAN_EUR,
    MAX_PRICE_RATIO, MIN_SELLER_RATING, MIN_SELLER_REVIEWS,
    ACCEPTED_CONDITIONS,
)
from watchlist import RARITY_KEYWORDS, RED_FLAGS, COUNTRY_VALUE_MULTIPLIERS


def _safe_float(val, default=0.0) -> float:
    try:
        return float(val or default)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0) -> int:
    try:
        return int(val or default)
    except (ValueError, TypeError):
        return default


def estimate_sell_price(median: float, condition: str, country: str = "US") -> float:
    mults = {
        "Mint (M)":              1.05,
        "Near Mint (NM or M-)":  1.00,
        "Very Good Plus (VG+)":  0.72,
        "Very Good (VG)":        0.48,
    }
    # Cerca parziale per gestire condition con "(stimata)" in coda
    mult = 0.70
    for key, val in mults.items():
        if key.lower() in (condition or "").lower():
            mult = val
            break
    country_mult = COUNTRY_VALUE_MULTIPLIERS.get(country, 1.0)
    return round(median * mult * country_mult, 2)


def calc_shipping_in(country: str) -> float:
    if country in ("Japan",):
        return SHIPPING_IN_JP
    if country in ("US", "Canada"):
        return SHIPPING_IN_US
    return SHIPPING_IN_EU


def calc_profit(listing_price: float, median: float,
                condition: str, seller_country: str = "US") -> dict:
    listing_price = _safe_float(listing_price)
    median        = _safe_float(median)
    ship_in       = calc_shipping_in(seller_country or "US")
    total_cost    = listing_price + ship_in + PACKAGING_COST
    est_sell      = estimate_sell_price(median, condition or "", seller_country or "US")
    fees          = round(est_sell * DISCOGS_FEE, 2)
    net           = round(est_sell - fees - SHIPPING_OUT - total_cost, 2)
    roi           = round(net / total_cost, 4) if total_cost > 0 else 0.0
    return {
        "listing_price":  listing_price,
        "shipping_in":    ship_in,
        "total_cost":     round(total_cost, 2),
        "est_sell_price": est_sell,
        "platform_fees":  fees,
        "gross_profit":   net,
        "roi":            roi,
    }


def find_rarity_signals(text: str) -> list:
    if not text:
        return []
    text_lower = text.lower()
    return [kw for kw in RARITY_KEYWORDS if kw in text_lower]


def find_red_flags(text: str) -> list:
    if not text:
        return []
    text_lower = text.lower()
    return [rf for rf in RED_FLAGS if rf in text_lower]


def detect_first_press_from_matrix(notes: str) -> bool:
    if not notes:
        return False
    return bool(re.search(r'\b(A[-\s]?1|1A|B[-\s]?1|1B)\b', notes, re.IGNORECASE))


def detect_engineer_initials(notes: str) -> list:
    if not notes:
        return []
    engineers = {
        "RL": "Robert Ludwig", "BG": "Bernie Grundman",
        "PORKY": "George Peckham", "ALLY": "George Peckham (alias)",
    }
    notes_upper = notes.upper()
    return [f"{k} ({v})" for k, v in engineers.items() if k in notes_upper]


def score_opportunity(opp: dict) -> float:
    score = 0.0

    roi    = _safe_float(opp.get("roi"))
    profit = _safe_float(opp.get("gross_profit"))
    wants  = _safe_int(opp.get("wantlist_count"))
    sale   = _safe_int(opp.get("num_for_sale"))
    rating = _safe_float(opp.get("seller_rating"), 100)
    reviews= _safe_int(opp.get("seller_reviews"))
    lp     = _safe_float(opp.get("listing_price"))
    med    = _safe_float(opp.get("median_price"), 1)
    cond   = (opp.get("condition") or "").lower()
    sigs   = opp.get("rarity_signals") or []
    flags  = opp.get("red_flags") or []

    # ROI (max 3 pts)
    if roi >= 1.50:      score += 3.0
    elif roi >= 1.00:    score += 2.5
    elif roi >= 0.75:    score += 2.0
    elif roi >= 0.60:    score += 1.5
    elif roi >= MIN_ROI: score += 1.0
    else:                score -= 1.0

    # Profitto assoluto (max 1.5 pts)
    if profit >= 80:     score += 1.5
    elif profit >= 50:   score += 1.0
    elif profit >= 30:   score += 0.5
    elif profit < MIN_PROFIT_EUR: score -= 0.5

    # Condizione (max 1.5 pts)
    if "mint (m)" == cond:             score += 1.5
    elif "near mint" in cond:          score += 1.2
    elif "very good plus" in cond:     score += 0.7
    elif "very good" in cond:          score += 0.0
    else:                              score -= 0.3

    # Domanda (max 1.5 pts)
    if wants >= 2000:    score += 1.5
    elif wants >= 1000:  score += 1.0
    elif wants >= 500:   score += 0.7
    elif wants >= 200:   score += 0.3
    elif wants >= 50:    score += 0.1

    # Liquidità (max 0.5 pts)
    if 1 <= sale <= 5:   score += 0.5
    elif sale <= 20:     score += 0.2
    elif sale >= 100:    score -= 0.3

    # Rarità (max 2 pts)
    score += min(len(sigs) * 0.4, 2.0)

    # Red flags (penalità)
    score -= len(flags) * 0.5

    # Seller (penalità)
    if rating < MIN_SELLER_RATING:   score -= 1.0
    if reviews < MIN_SELLER_REVIEWS: score -= 0.5

    # Prezzo molto sotto mediana (bonus)
    ratio = lp / med if med > 0 else 1
    if ratio <= 0.30:    score += 0.5
    elif ratio <= 0.45:  score += 0.3

    return round(max(1.0, min(10.0, score)), 1)


def passes_prefilter(listing: dict, median: float) -> tuple:
    """Legacy — usato solo se si torna alla strategia listing-by-listing."""
    condition = (listing.get("condition") or "")
    if condition not in ACCEPTED_CONDITIONS:
        return False, f"Condizione '{condition}' non accettata"
    if _safe_float(median) < MIN_MEDIAN_EUR:
        return False, f"Mediana €{median:.0f} < soglia"
    p_data = listing.get("price") or 0
    price  = float(p_data.get("value", 0) if isinstance(p_data, dict) else p_data or 0)
    if price <= 0:
        return False, "Prezzo zero"
    if median > 0 and price > median * MAX_PRICE_RATIO:
        return False, f"Prezzo €{price:.0f} > {MAX_PRICE_RATIO*100:.0f}% mediana"
    return True, ""
