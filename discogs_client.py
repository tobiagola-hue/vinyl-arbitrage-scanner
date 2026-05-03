"""
VINYL ARBITRAGE SCANNER — Discogs Client v4
BUGFIX DEFINITIVO: /marketplace/search richiede OAuth, non funziona con token.
Nuova strategia: usiamo lowest_price dal release endpoint + price_suggestions.
"""
import time
import requests
from config import (
    DISCOGS_TOKEN, DISCOGS_BASE_URL, DISCOGS_USER_AGENT,
    RATE_LIMIT_SLEEP, REQUEST_TIMEOUT, MAX_RETRIES
)

HEADERS = {
    "Authorization": f"Discogs token={DISCOGS_TOKEN}",
    "User-Agent": DISCOGS_USER_AGENT,
}


def _get(endpoint: str, params: dict = None) -> dict | None:
    url = f"{DISCOGS_BASE_URL}{endpoint}"
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(
                url, headers=HEADERS,
                params=params or {},
                timeout=REQUEST_TIMEOUT
            )
            time.sleep(RATE_LIMIT_SLEEP)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                print(f"  Rate limit — attendo 60s...")
                time.sleep(60)
            elif r.status_code in (401, 403):
                print(f"  Auth error {r.status_code} — endpoint richiede OAuth")
                return None
            elif r.status_code == 404:
                return None
            else:
                return None
        except requests.RequestException as e:
            print(f"  Errore rete (tentativo {attempt+1}): {e}")
            time.sleep(3)
    return None


def search_releases(query: str, page: int = 1) -> dict | None:
    """Cerca release nel database Discogs."""
    return _get("/database/search", {
        "q":        query,
        "type":     "release",
        "format":   "vinyl",
        "page":     page,
        "per_page": 10,
    })


def get_release_details(release_id: int) -> dict | None:
    """
    Dettaglio release. Contiene:
    - lowest_price: prezzo più basso attuale in marketplace
    - num_for_sale: quanti in vendita
    - community.want / community.have
    """
    return _get(f"/releases/{release_id}")


def get_price_suggestions(release_id: int) -> dict | None:
    """
    Prezzi suggeriti per condizione (calcolati da vendite reali).
    Funziona con token semplice.
    Restituisce mediane per: Mint, Near Mint, VG+, VG, G+
    """
    return _get(f"/marketplace/price_suggestions/{release_id}")


def get_marketplace_url(release_id: int) -> str:
    """URL diretto al marketplace per questa release, ordinato per prezzo."""
    return (
        f"https://www.discogs.com/sell/release/{release_id}"
        f"?status=For+Sale&sort=price%2Casc"
    )
