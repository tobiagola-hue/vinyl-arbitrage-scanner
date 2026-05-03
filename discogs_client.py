"""
VINYL ARBITRAGE SCANNER — Discogs Client v5
Supporta OAuth 1.0a (pieno accesso) e token semplice (fallback).
Gestisce tutti i casi di errore possibili.
"""
import os
import time
import requests

try:
    from requests_oauthlib import OAuth1
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

from config import (
    DISCOGS_BASE_URL, DISCOGS_USER_AGENT,
    RATE_LIMIT_SLEEP, REQUEST_TIMEOUT, MAX_RETRIES,
    DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET,
    DISCOGS_ACCESS_TOKEN, DISCOGS_ACCESS_SECRET,
    DISCOGS_TOKEN,
)

# ── Scegli modalità autenticazione ───────────────────
HAS_OAUTH = (
    OAUTH_AVAILABLE and
    all([DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET,
         DISCOGS_ACCESS_TOKEN, DISCOGS_ACCESS_SECRET])
)

HEADERS = {"User-Agent": DISCOGS_USER_AGENT}
AUTH    = None

if HAS_OAUTH:
    AUTH = OAuth1(
        DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET,
        DISCOGS_ACCESS_TOKEN, DISCOGS_ACCESS_SECRET
    )
elif DISCOGS_TOKEN:
    HEADERS["Authorization"] = f"Discogs token={DISCOGS_TOKEN}"


def _get(endpoint: str, params: dict = None) -> dict | None:
    """GET con retry automatico, rate limiting e gestione errori."""
    url = f"{DISCOGS_BASE_URL}{endpoint}"
    for attempt in range(MAX_RETRIES):
        try:
            kwargs = {
                "headers": HEADERS,
                "params":  params or {},
                "timeout": REQUEST_TIMEOUT,
            }
            if AUTH:
                kwargs["auth"] = AUTH

            r = requests.get(url, **kwargs)
            time.sleep(RATE_LIMIT_SLEEP)

            if r.status_code == 200:
                try:
                    return r.json()
                except Exception:
                    return None

            elif r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 60))
                print(f"  Rate limit — attendo {wait}s...")
                time.sleep(wait)
                continue

            elif r.status_code == 404:
                return None

            elif r.status_code in (401, 403):
                # Endpoint richiede OAuth — non ritentare
                return None

            elif r.status_code in (500, 502, 503, 504):
                # Errore server Discogs — aspetta e riprova
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                return None

            else:
                return None

        except requests.Timeout:
            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
                continue
            return None
        except requests.ConnectionError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
                continue
            return None
        except Exception:
            return None

    return None


def search_releases(query: str, page: int = 1) -> dict | None:
    """Cerca release nel database Discogs per query testuale."""
    if not query or not query.strip():
        return None
    return _get("/database/search", {
        "q":        query.strip(),
        "type":     "release",
        "format":   "vinyl",
        "page":     page,
        "per_page": 10,
    })


def get_release_details(release_id: int) -> dict | None:
    """Dettaglio release: lowest_price, num_for_sale, community, labels, artists."""
    if not release_id:
        return None
    return _get(f"/releases/{release_id}")


def get_price_suggestions(release_id: int) -> dict | None:
    """
    Mediane ufficiali per condizione (calcolate da vendite reali).
    Richiede OAuth — ritorna None con token semplice.
    """
    if not release_id:
        return None
    return _get(f"/marketplace/price_suggestions/{release_id}")


def get_marketplace_listings(release_id: int) -> list:
    """
    Listing attivi ordinati per prezzo.
    Richiede OAuth — ritorna [] con token semplice.
    """
    if not release_id or not HAS_OAUTH:
        return []
    data = _get("/marketplace/search", {
        "release_id": release_id,
        "status":     "For Sale",
        "sort":       "price",
        "sort_order": "asc",
        "per_page":   20,
    })
    if not data:
        return []
    # L'API può restituire 'results' o 'listings' a seconda della versione
    return data.get("results") or data.get("listings") or []


def get_marketplace_url(release_id: int) -> str:
    """URL diretto al marketplace Discogs, ordinato per prezzo crescente."""
    return (
        f"https://www.discogs.com/sell/release/{release_id}"
        f"?status=For+Sale&sort=price%2Casc"
    )


def get_release_url(release_id: int) -> str:
    """URL scheda disco su Discogs."""
    return f"https://www.discogs.com/release/{release_id}"
