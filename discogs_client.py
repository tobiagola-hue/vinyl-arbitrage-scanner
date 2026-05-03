"""
VINYL ARBITRAGE SCANNER — Discogs Client v3
Bugfix: marketplace search restituisce "results", non "listings".
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
    """Cerca nel database Discogs — restituisce chiave 'results'."""
    return _get("/database/search", {
        "q":        query,
        "type":     "release",
        "format":   "vinyl",
        "page":     page,
        "per_page": 10,
    })


def get_release_details(release_id: int) -> dict | None:
    return _get(f"/releases/{release_id}")


def get_marketplace_listings(release_id: int) -> list:
    """
    Restituisce lista di listing attivi per questa release.
    BUGFIX: l'endpoint /marketplace/search restituisce 'results' non 'listings'.
    Ordina per prezzo crescente, filtra solo For Sale.
    """
    data = _get("/marketplace/search", {
        "release_id": release_id,
        "status":     "For Sale",
        "sort":       "price",
        "sort_order": "asc",
        "per_page":   25,
    })
    if not data:
        return []

    # Debug: mostra le chiavi restituite se non trova results
    results = data.get("results") or data.get("listings") or []
    if not results and data:
        keys = list(data.keys())
        print(f"      ↳ Marketplace response keys: {keys}")

    return results


def get_price_stats(release_id: int) -> dict | None:
    """Prezzi suggeriti Discogs per condizione (mediana da vendite reali)."""
    return _get(f"/marketplace/price_suggestions/{release_id}")
