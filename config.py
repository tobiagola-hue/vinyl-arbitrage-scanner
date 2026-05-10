import os

# API KEYS
DISCOGS_CONSUMER_KEY    = os.getenv("DISCOGS_CONSUMER_KEY", "")
DISCOGS_CONSUMER_SECRET = os.getenv("DISCOGS_CONSUMER_SECRET", "")
DISCOGS_ACCESS_TOKEN    = os.getenv("DISCOGS_ACCESS_TOKEN", "")
DISCOGS_ACCESS_SECRET   = os.getenv("DISCOGS_ACCESS_SECRET", "")
DISCOGS_TOKEN           = os.getenv("DISCOGS_TOKEN", "")
TELEGRAM_BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID", "")

# SOGLIE
MIN_ROI          = 0.15     # 15% ROI minimo (realistico dopo spedizioni)
MIN_PROFIT_EUR   = 8.0      # Profitto netto minimo €
MIN_SCORE        = 4.0      # Score minimo per alert
MAX_PRICE_RATIO  = 0.55     # Compra solo se prezzo <= 55% mediana
MIN_MEDIAN_EUR   = 15.0

# SELLER
MIN_SELLER_RATING   = 97.0
MIN_SELLER_REVIEWS  = 5

# FEE
DISCOGS_FEE  = 0.11
EBAY_FEE     = 0.145

# SPEDIZIONI (€)
SHIPPING_IN_EU  = 6.0
SHIPPING_IN_US  = 10.0
SHIPPING_IN_JP  = 15.0
SHIPPING_OUT    = 7.0
PACKAGING_COST  = 1.20

ACCEPTED_CONDITIONS = [
    "Mint (M)",
    "Near Mint (NM or M-)",
    "Very Good Plus (VG+)",
]

DISCOGS_BASE_URL    = "https://api.discogs.com"
DISCOGS_USER_AGENT  = "VinylArbitrageScanner/1.0"
RATE_LIMIT_SLEEP    = 1.2
REQUEST_TIMEOUT     = 15
MAX_RETRIES         = 3
DB_PATH             = "vinyl_arbitrage.db"
MAX_RELEASES_PER_ARTIST  = 30
MAX_LISTINGS_PER_RELEASE = 10
