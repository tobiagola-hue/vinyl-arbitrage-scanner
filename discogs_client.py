"""
VINYL ARBITRAGE SCANNER — Discogs Client v2
Bugfix: parametri search corretti per ottenere risultati pertinenti.
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
            elif r.status_code == 404:
                return None
            else:
                print(f"  HTTP {r.status_code} su {endpoint}")
                return None
        except requests.RequestException as e:
            print(f"  Errore rete (tentativo {attempt+1}): {e}")
            time.sleep(3)
    return None


def search_releases(query: str, page: int = 1) -> dict | None:
    """
    Cerca nel database Discogs.
    IMPORTANTE: usa il parametro 'q' per full-text search,
    con type=release e format=vinyl.
    """
    params = {
        "q":        query,          # Query libera — campo principale
        "type":     "release",      # Solo release (non master/label/artist)
        "format":   "vinyl",        # Solo vinile
        "page":     page,
        "per_page": 10,
    }
    return _get("/database/search", params)


def get_release_details(release_id: int) -> dict | None:
    return _get(f"/releases/{release_id}")


def get_marketplace_listings(release_id: int) -> dict | None:
    """Listing attivi sul marketplace per questa release, ordinati per prezzo."""
    return _get("/marketplace/search", {
        "release_id": release_id,
        "sort":       "price",
        "sort_order": "asc",
        "per_page":   10,
    })


def get_price_stats(release_id: int) -> dict | None:
    """Suggerimenti prezzo ufficiali Discogs per condizione."""
    return _get(f"/marketplace/price_suggestions/{release_id}")
