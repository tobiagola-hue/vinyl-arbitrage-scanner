"""
VINYL ARBITRAGE SCANNER — Config
Tutte le variabili d'ambiente e soglie di business.
"""
import os

# ─────────────────────────────────────────────
# API KEYS (da GitHub Secrets / .env locale)
# ─────────────────────────────────────────────
DISCOGS_TOKEN       = os.getenv("DISCOGS_TOKEN", "")
TELEGRAM_BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID", "")

# ─────────────────────────────────────────────
# SOGLIE DI BUSINESS
# ─────────────────────────────────────────────
MIN_ROI             = 0.40      # ROI minimo 40% dopo tutte le fee
MIN_PROFIT_EUR      = 15.0      # Profitto netto minimo in €
MIN_SCORE           = 7.0       # Score minimo per ricevere alert Telegram (1-10)
MAX_PRICE_RATIO     = 0.62      # Compra solo se prezzo <= 62% della mediana Discogs
MIN_MEDIAN_EUR      = 20.0      # Ignora release con mediana < 20€ (non vale il tempo)
MIN_SELLER_RATING   = 97.0      # Rating minimo venditore (%)
MIN_SELLER_REVIEWS  = 5         # Numero minimo feedback venditore

# ─────────────────────────────────────────────
# FEE PIATTAFORME (decimale)
# ─────────────────────────────────────────────
DISCOGS_FEE         = 0.11      # 8% seller fee + ~3% payment processing
EBAY_FEE            = 0.145     # ~14.5% totale
PAYPAL_FEE          = 0.034     # Per vendite fuori piattaforma

# ─────────────────────────────────────────────
# COSTI SPEDIZIONE STIMATI (€)
# ─────────────────────────────────────────────
SHIPPING_IN_EU      = 6.0       # Ricezione da venditore EU
SHIPPING_IN_US      = 10.0      # Ricezione da venditore USA
SHIPPING_IN_JP      = 15.0      # Ricezione da venditore Giappone
SHIPPING_OUT        = 7.0       # Spedizione verso acquirente
PACKAGING_COST      = 1.20      # Busta rigida + cartone

# ─────────────────────────────────────────────
# CONDIZIONI ACCETTATE (Goldmine Standard)
# ─────────────────────────────────────────────
ACCEPTED_CONDITIONS = [
    "Mint (M)",
    "Near Mint (NM or M-)",
    "Very Good Plus (VG+)",
]

# ─────────────────────────────────────────────
# API SETTINGS
# ─────────────────────────────────────────────
DISCOGS_BASE_URL    = "https://api.discogs.com"
DISCOGS_USER_AGENT  = "VinylArbitrageScanner/1.0 +github.com/yourusername/vinyl-arbitrage-scanner"
RATE_LIMIT_SLEEP    = 1.1       # Secondi tra request (Discogs limit: 60/min auth)
REQUEST_TIMEOUT     = 15        # Secondi timeout per request
MAX_RETRIES         = 3         # Retry su errori temporanei

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
DB_PATH = "vinyl_arbitrage.db"

# ─────────────────────────────────────────────
# SCAN SETTINGS
# ─────────────────────────────────────────────
MAX_RELEASES_PER_ARTIST = 30    # Max release da controllare per artista
MAX_RELEASES_PER_LABEL  = 20    # Max release da controllare per label
MAX_LISTINGS_PER_RELEASE = 10   # Max listing da analizzare per release
