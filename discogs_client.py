import os, time, requests
try:
    from requests_oauthlib import OAuth1
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

from config import (
    DISCOGS_BASE_URL, DISCOGS_USER_AGENT, RATE_LIMIT_SLEEP,
    REQUEST_TIMEOUT, MAX_RETRIES,
    DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET,
    DISCOGS_ACCESS_TOKEN, DISCOGS_ACCESS_SECRET, DISCOGS_TOKEN,
)

HAS_OAUTH = OAUTH_AVAILABLE and all([
    DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET,
    DISCOGS_ACCESS_TOKEN, DISCOGS_ACCESS_SECRET
])

HEADERS = {"User-Agent": DISCOGS_USER_AGENT}
AUTH = None
if HAS_OAUTH:
    AUTH = OAuth1(DISCOGS_CONSUMER_KEY, DISCOGS_CONSUMER_SECRET,
                  DISCOGS_ACCESS_TOKEN, DISCOGS_ACCESS_SECRET)
elif DISCOGS_TOKEN:
    HEADERS["Authorization"] = f"Discogs token={DISCOGS_TOKEN}"


def _get(endpoint, params=None):
    url = f"{DISCOGS_BASE_URL}{endpoint}"
    for attempt in range(MAX_RETRIES):
        try:
            kw = {"headers": HEADERS, "params": params or {}, "timeout": REQUEST_TIMEOUT}
            if AUTH:
                kw["auth"] = AUTH
            r = requests.get(url, **kw)
            time.sleep(RATE_LIMIT_SLEEP)
            if r.status_code == 200:
                try: return r.json()
                except Exception: return None
            if r.status_code == 429:
                time.sleep(60)
            elif r.status_code in (401, 403, 404):
                return None
            elif r.status_code in (500, 502, 503):
                time.sleep(5 * (attempt + 1))
        except requests.Timeout:
            time.sleep(3)
        except requests.ConnectionError:
            time.sleep(5)
        except Exception:
            return None
    return None


def search_releases(query, page=1):
    return _get("/database/search", {
        "q": query, "type": "release",
        "format": "vinyl", "page": page, "per_page": 10,
    })


def get_release_details(release_id):
    return _get(f"/releases/{release_id}")


def get_price_suggestions(release_id):
    return _get(f"/marketplace/price_suggestions/{release_id}")


def get_marketplace_listings(release_id):
    if not HAS_OAUTH:
        return []
    data = _get("/marketplace/search", {
        "release_id": release_id, "status": "For Sale",
        "sort": "price", "sort_order": "asc", "per_page": 20,
    })
    if not data:
        return []
    return data.get("results") or data.get("listings") or []


def get_marketplace_url(release_id):
    return (f"https://www.discogs.com/sell/release/{release_id}"
            f"?status=For+Sale&sort=price%2Casc")


def get_release_url(release_id):
    return f"https://www.discogs.com/release/{release_id}"
