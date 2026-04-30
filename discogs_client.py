"""
VINYL ARBITRAGE SCANNER — Discogs Client
Tutte le chiamate all'API Discogs con rate limiting automatico.
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
            r = requests.get(url, headers=HEADERS, params=params or {}, timeout=REQUEST_TIMEOUT)
            time.sleep(RATE_LIMIT_SLEEP)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                print(f"  Rate limit — attendo 60s...")
                time.sleep(60)
            elif r.status_code == 404:
                return None
            else:
                print(f"  HTTP {r.status_code} su {url}")
        except requests.RequestException as e:
            print(f"  Errore rete: {e} (tentativo {attempt+1}/{MAX_RETRIES})")
            time.sleep(3)
    return None


def get_artist_releases(artist_id: int, page: int = 1, per_page: int = 50) -> dict | None:
    return _get(f"/artists/{artist_id}/releases", {
        "sort": "year", "sort_order": "desc",
        "page": page, "per_page": per_page
    })


def get_master_versions(master_id: int, page: int = 1, per_page: int = 100) -> dict | None:
    return _get(f"/masters/{master_id}/versions", {
        "format": "Vinyl", "page": page, "per_page": per_page
    })


def get_release_details(release_id: int) -> dict | None:
    return _get(f"/releases/{release_id}")


def get_marketplace_listings(release_id: int, condition: str = None) -> dict | None:
    params = {"release_id": release_id, "sort": "price", "sort_order": "asc", "per_page": 50}
    if condition:
        params["condition"] = condition
    return _get("/marketplace/search", params)


def get_price_stats(release_id: int) -> dict | None:
    """Statistiche prezzi: mediana, min, max (solo per utenti autenticati)."""
    return _get(f"/marketplace/price_suggestions/{release_id}")


def search_releases(query: str = None, artist: str = None,
                    release_title: str = None, catno: str = None,
                    page: int = 1) -> dict | None:
    params = {"type": "release", "format": "vinyl", "page": page, "per_page": 25}
    if query:       params["q"] = query
    if artist:      params["artist"] = artist
    if release_title: params["release_title"] = release_title
    if catno:       params["catno"] = catno
    return _get("/database/search", params)


def get_label_releases(label_id: int, page: int = 1) -> dict | None:
    return _get(f"/labels/{label_id}/releases", {"page": page, "per_page": 50})
