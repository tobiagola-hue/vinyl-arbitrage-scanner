import os

# DISCOGS
DISCOGS_CONSUMER_KEY    = os.getenv("DISCOGS_CONSUMER_KEY", "")
DISCOGS_CONSUMER_SECRET = os.getenv("DISCOGS_CONSUMER_SECRET", "")
DISCOGS_ACCESS_TOKEN    = os.getenv("DISCOGS_ACCESS_TOKEN", "")
DISCOGS_ACCESS_SECRET   = os.getenv("DISCOGS_ACCESS_SECRET", "")
DISCOGS_TOKEN           = os.getenv("DISCOGS_TOKEN", "")

# TELEGRAM
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# EBAY (App ID da developer.ebay.com)
EBAY_APP_ID = os.getenv("EBAY_APP_ID", "")

# SOGLIE BUSINESS
MIN_ROI        = 0.15
MIN_PROFIT_EUR = 8.0
MIN_SCORE      = 4.0

# Expensive mode: Discogs->Discogs
MAX_RATIO_EXPENSIVE  = 0.62
MIN_MEDIAN_EXPENSIVE = 60.0
MIN_WANT_EXPENSIVE   = 25

# Midvalue mode: eBay->Discogs
MAX_RATIO_MIDVALUE   = 0.58
MIN_MEDIAN_MIDVALUE  = 35.0
MIN_WANT_MIDVALUE    = 15

# FEE E SPEDIZIONI
DISCOGS_FEE    = 0.11
SHIPPING_IN_EU = 6.0
SHIPPING_IN_US = 12.0
SHIPPING_IN_JP = 18.0
SHIPPING_OUT   = 7.0
PACKAGING_COST = 1.20

ACCEPTED_CONDITIONS = [
    "Mint (M)",
    "Near Mint (NM or M-)",
    "Very Good Plus (VG+)",
]

DISCOGS_BASE_URL   = "https://api.discogs.com"
DISCOGS_USER_AGENT = "VinylArbitrageScanner/1.0"
RATE_LIMIT_SLEEP   = 1.2
REQUEST_TIMEOUT    = 15
MAX_RETRIES        = 3
DB_PATH            = "vinyl_arbitrage.db"
