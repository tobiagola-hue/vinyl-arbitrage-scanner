"""
VINYL ARBITRAGE SCANNER — Scorer
Calcola ROI, profitto netto e score opportunità (1-10).
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
    """
    Stima il prezzo di vendita realistico in base alla condizione
    e al mercato corrente (mediana Discogs ± sconto condizione).
    """
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
    """Stima costo spedizione in entrata in base al paese del venditore."""
    if seller_country in ("Japan",):
        return SHIPPING_IN_JP
    if seller_country in ("US", "Canada"):
        return SHIPPING_IN_US
    return SHIPPING_IN_EU


def calc_profit(listing_price: float, median: float,
                condition: str, seller_country: str = "US") -> dict:
    """
    Calcola profitto netto e ROI completo.
    Ritorna dict con tutti i dettagli del calcolo.
    """
    ship_in  = calc_shipping_in(seller_country)
    total_cost = listing_price + ship_in + PACKAGING_COST

    est_sell  = estimate_sell_price(median, condition, seller_country)
    fees      = round(est_sell * DISCOGS_FEE, 2)
    ship_out  = SHIPPING_OUT
    net       = round(est_sell - fees - ship_out - total_cost, 2)
    roi       = round(net / total_cost, 4) if total_cost > 0 else 0

    return {
        "listing_price":  listing_price,
        "shipping_in":    ship_in,
        "packaging":      PACKAGING_COST,
        "total_cost":     round(total_cost, 2),
        "est_sell_price": est_sell,
        "platform_fees":  fees,
        "shipping_out":   ship_out,
        "gross_profit":   round(net, 2),
        "roi":            roi,
        "roi_pct":        f"{roi*100:.1f}%",
    }


# ─────────────────────────────────────────────
# ANALISI RARITÀ
# ─────────────────────────────────────────────

def find_rarity_signals(text: str) -> list[str]:
    """Trova keyword di rarità nel testo del listing."""
    text_lower = text.lower()
    return [kw for kw in RARITY_KEYWORDS if kw in text_lower]


def find_red_flags(text: str) -> list[str]:
    """Trova red flag (ristampe, problemi) nel testo del listing."""
    text_lower = text.lower()
    return [rf for rf in RED_FLAGS if rf in text_lower]


def detect_first_press_from_matrix(notes: str) -> bool:
    """
    Cerca indicatori di first press nel dead wax / matrix scraped dalle note.
    Pattern: A1/B1, A-1/B-1, 1A/1B nel campo matrix/runout.
    """
    if not notes:
        return False
    pattern = r'\b(A[-\s]?1|1A|B[-\s]?1|1B)\b'
    return bool(re.search(pattern, notes, re.IGNORECASE))


def detect_engineer_initials(notes: str) -> list[str]:
    """
    Identifica iniziali di mastering engineer famosi nel dead wax.
    Questi aumentano il valore (RL = Robert Ludwig, BG = Bernie Grundman, ecc.)
    """
    if not notes:
        return []
    found = []
    engineers = {
        "RL":    "Robert Ludwig",
        "BG":    "Bernie Grundman",
        "PORKY": "George Peckham",
        "ALLY":  "George Peckham (alias)",
        "SH":    "Sterling Sound",
        "PR":    "Phil Ek",
    }
    notes_upper = notes.upper()
    for initials, name in engineers.items():
        if initials in notes_upper:
            found.append(f"{initials} ({name})")
    return found


# ─────────────────────────────────────────────
# SCORING PRINCIPALE (1-10)
# ─────────────────────────────────────────────

def score_opportunity(opp: dict) -> float:
    """
    Assegna un punteggio da 1.0 a 10.0 all'opportunità.
    Score >= 7 → invia alert Telegram.

    Parametri attesi in opp:
      roi, gross_profit, condition, wantlist_count, num_for_sale,
      rarity_signals, red_flags, seller_rating, seller_reviews,
      listing_price, median_price, notes (optional)
    """
    score = 0.0

    # ── 1. ROI (max 3 punti) ──────────────────────────
    roi = opp.get("roi", 0)
    if roi >= 1.50:     score += 3.0   # ROI +150% = eccezionale
    elif roi >= 1.00:   score += 2.5
    elif roi >= 0.75:   score += 2.0
    elif roi >= 0.60:   score += 1.5
    elif roi >= MIN_ROI: score += 1.0
    else:               score -= 1.0   # ROI insufficiente, penalità

    # ── 2. Profitto assoluto (max 1.5 punti) ─────────
    profit = opp.get("gross_profit", 0)
    if profit >= 80:    score += 1.5
    elif profit >= 50:  score += 1.0
    elif profit >= 30:  score += 0.5
    elif profit < MIN_PROFIT_EUR: score -= 0.5

    # ── 3. Condizione disco (max 1.5 punti) ──────────
    condition = opp.get("condition", "")
    if condition == "Mint (M)":                  score += 1.5
    elif condition == "Near Mint (NM or M-)":    score += 1.2
    elif condition == "Very Good Plus (VG+)":    score += 0.7
    elif condition == "Very Good (VG)":          score += 0.0
    else:                                        score -= 0.5

    # ── 4. Domanda (wantlist Discogs) (max 1.5 punti) 
    wants = opp.get("wantlist_count", 0)
    if wants >= 2000:   score += 1.5
    elif wants >= 1000: score += 1.0
    elif wants >= 500:  score += 0.7
    elif wants >= 200:  score += 0.3

    # ── 5. Liquidità (quanti in vendita ora) (max 0.5 punti) ──
    for_sale = opp.get("num_for_sale", 0)
    if 1 <= for_sale <= 5:   score += 0.5    # Raro e disponibile
    elif for_sale <= 20:     score += 0.2
    elif for_sale >= 100:    score -= 0.3    # Molto comune, margine basso

    # ── 6. Segnali rarità (max 2 punti) ──────────────
    signals = opp.get("rarity_signals", [])
    signal_score = min(len(signals) * 0.4, 2.0)
    score += signal_score

    # ── 7. Red flags (penalità) ───────────────────────
    flags = opp.get("red_flags", [])
    score -= len(flags) * 0.5

    # ── 8. Seller reputation (penalità) ──────────────
    rating  = opp.get("seller_rating", 100)
    reviews = opp.get("seller_reviews", 0)
    if rating < MIN_SELLER_RATING:  score -= 1.0
    if reviews < MIN_SELLER_REVIEWS: score -= 0.5

    # ── 9. Prezzo molto sotto mediana (bonus) ────────
    listing = opp.get("listing_price", 0)
    median  = opp.get("median_price", 1)
    ratio = listing / median if median > 0 else 1
    if ratio <= 0.30:   score += 0.5    # Mega affare
    elif ratio <= 0.45: score += 0.3

    # Clamp tra 1 e 10
    return round(max(1.0, min(10.0, score)), 1)


# ─────────────────────────────────────────────
# FILTRO RAPIDO PRE-SCORING
# ─────────────────────────────────────────────

def passes_prefilter(listing: dict, median: float) -> tuple[bool, str]:
    """
    Filtro rapido per scartare listing ovviamente non validi,
    prima di fare il calcolo completo.
    Ritorna (True, "") se passa o (False, "motivo") se scarta.
    """
    condition = listing.get("condition", {}).get("id", "")

    # Condizione minima
    if condition not in ACCEPTED_CONDITIONS:
        return False, f"Condizione '{condition}' non accettata"

    # Mediana troppo bassa (disco comune)
    if median < MIN_MEDIAN_EUR:
        return False, f"Mediana €{median} sotto soglia €{MIN_MEDIAN_EUR}"

    price = listing.get("price", {}).get("value", 0)

    # Prezzo troppo alto rispetto alla mediana (nessun margine)
    if median > 0 and price > median * MAX_PRICE_RATIO:
        return False, f"Prezzo €{price} > {MAX_PRICE_RATIO*100:.0f}% della mediana €{median}"

    return True, ""
