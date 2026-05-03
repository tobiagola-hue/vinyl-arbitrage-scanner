"""
VINYL ARBITRAGE SCANNER — Scorer v2
Bugfix: condition era trattata come dict invece che stringa.
"""
import re
from config import (
    DISCOGS_FEE, SHIPPING_OUT, PACKAGING_COST,
    SHIPPING_IN_EU, SHIPPING_IN_US, SHIPPING_IN_JP,
    MIN_ROI, MIN_PROFIT_EUR, MIN_MEDIAN_EUR,
    MAX_PRICE_RATIO, MIN_SELLER_RATING, MIN_SELLER_REVIEWS,
    ACCEPTED_CONDITIONS
)
from watchlist import RARITY_KEYWORDS, RED_FLAGS, COUNTRY_VALUE_MULTIPLIERS


# ─────────────────────────────────────────────
# CALCOLO PROFITTO
# ─────────────────────────────────────────────

def estimate_sell_price(median: float, condition: str, country_buy: str = "US") -> float:
    condition_multipliers = {
        "Mint (M)":              1.05,
        "Near Mint (NM or M-)":  1.00,
        "Very Good Plus (VG+)":  0.72,
        "Very Good (VG)":        0.48,
    }
    mult = condition_multipliers.get(condition, 0.70)
    country_mult = COUNTRY_VALUE_MULTIPLIERS.get(country_buy, 1.0)
    return round(median * mult * country_mult, 2)


def calc_shipping_in(seller_country: str) -> float:
    if seller_country in ("Japan",):
        return SHIPPING_IN_JP
    if seller_country in ("US", "Canada"):
        return SHIPPING_IN_US
    return SHIPPING_IN_EU


def calc_profit(listing_price: float, median: float,
                condition: str, seller_country: str = "US") -> dict:
    ship_in    = calc_shipping_in(seller_country)
    total_cost = listing_price + ship_in + PACKAGING_COST
    est_sell   = estimate_sell_price(median, condition, seller_country)
    fees       = round(est_sell * DISCOGS_FEE, 2)
    ship_out   = SHIPPING_OUT
    net        = round(est_sell - fees - ship_out - total_cost, 2)
    roi        = round(net / total_cost, 4) if total_cost > 0 else 0

    return {
        "listing_price":  listing_price,
        "shipping_in":    ship_in,
        "total_cost":     round(total_cost, 2),
        "est_sell_price": est_sell,
        "platform_fees":  fees,
        "gross_profit":   net,
        "roi":            roi,
    }


# ─────────────────────────────────────────────
# ANALISI RARITÀ
# ─────────────────────────────────────────────

def find_rarity_signals(text: str) -> list:
    text_lower = text.lower()
    return [kw for kw in RARITY_KEYWORDS if kw in text_lower]


def find_red_flags(text: str) -> list:
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


# ─────────────────────────────────────────────
# SCORING 1-10
# ─────────────────────────────────────────────

def score_opportunity(opp: dict) -> float:
    score = 0.0

    roi = opp.get("roi", 0)
    if roi >= 1.50:      score += 3.0
    elif roi >= 1.00:    score += 2.5
    elif roi >= 0.75:    score += 2.0
    elif roi >= 0.60:    score += 1.5
    elif roi >= MIN_ROI: score += 1.0
    else:                score -= 1.0

    profit = opp.get("gross_profit", 0)
    if profit >= 80:     score += 1.5
    elif profit >= 50:   score += 1.0
    elif profit >= 30:   score += 0.5
    elif profit < MIN_PROFIT_EUR: score -= 0.5

    condition = opp.get("condition", "")
    if "Mint (M)" == condition:                score += 1.5
    elif "Near Mint" in condition:             score += 1.2
    elif "Very Good Plus" in condition:        score += 0.7
    elif "Very Good" in condition:             score += 0.0
    else:                                      score -= 0.5

    wants = opp.get("wantlist_count", 0)
    if wants >= 2000:    score += 1.5
    elif wants >= 1000:  score += 1.0
    elif wants >= 500:   score += 0.7
    elif wants >= 200:   score += 0.3
    elif wants >= 50:    score += 0.1

    for_sale = opp.get("num_for_sale", 0)
    if 1 <= for_sale <= 5:   score += 0.5
    elif for_sale <= 20:     score += 0.2
    elif for_sale >= 100:    score -= 0.3

    signals = opp.get("rarity_signals", [])
    score += min(len(signals) * 0.4, 2.0)

    flags = opp.get("red_flags", [])
    score -= len(flags) * 0.5

    rating  = opp.get("seller_rating", 100)
    reviews = opp.get("seller_reviews", 0)
    if rating < MIN_SELLER_RATING:   score -= 1.0
    if reviews < MIN_SELLER_REVIEWS: score -= 0.5

    listing = opp.get("listing_price", 0)
    median  = opp.get("median_price", 1)
    ratio = listing / median if median > 0 else 1
    if ratio <= 0.30:    score += 0.5
    elif ratio <= 0.45:  score += 0.3

    return round(max(1.0, min(10.0, score)), 1)


# ─────────────────────────────────────────────
# PRE-FILTRO — BUGFIX: condition è una stringa!
# ─────────────────────────────────────────────

def passes_prefilter(listing: dict, median: float) -> tuple:
    """
    BUGFIX v2: Discogs restituisce 'condition' come stringa semplice,
    NON come dict con chiave 'id'.
    """
    # ✅ Corretto: condition è una stringa diretta
    condition = listing.get("condition", "") or ""

    # Log debug per capire cosa arriva
    if not condition:
        return False, "Condizione mancante"

    if condition not in ACCEPTED_CONDITIONS:
        return False, f"Condizione '{condition}' non accettata (accettate: {ACCEPTED_CONDITIONS})"

    if median < MIN_MEDIAN_EUR:
        return False, f"Mediana €{median:.0f} < soglia €{MIN_MEDIAN_EUR}"

    # ✅ Corretto: price è un dict {"value": X, "currency": "EUR"}
    price_data = listing.get("price") or {}
    if isinstance(price_data, dict):
        price = float(price_data.get("value", 0) or 0)
    else:
        price = float(price_data or 0)

    if price <= 0:
        return False, "Prezzo mancante o zero"

    if median > 0 and price > median * MAX_PRICE_RATIO:
        return False, f"Prezzo €{price:.0f} > {MAX_PRICE_RATIO*100:.0f}% mediana €{median:.0f}"

    return True, ""
