"""
VINYL ARBITRAGE SCANNER — Watchlist
Definisce cosa monitorare: artisti, label, ricerche specifiche.
Personalizza questa lista in base al tuo mercato e competenze.

Tier A = Alta liquidità + alto margine (sempre attivi)
Tier B = Opportunistici (buoni mercati ma meno certi)
Tier C = Artisti specifici che conosci bene
"""

# ─────────────────────────────────────────────
# WATCHLIST PRINCIPALE
# Ogni entry ha:
#   name   → nome leggibile (solo per log)
#   type   → "artist" | "label" | "search"
#   id     → Discogs ID (per artist/label)
#   query  → stringa di ricerca (per type="search")
#   tier   → "A" | "B" | "C"
# ─────────────────────────────────────────────
WATCHLIST = [

    # ── TIER A — Jazz Originale ─────────────────────────
    # Pressature Blue Note anni '50-'60 valgono centinaia/migliaia
    {"name": "Miles Davis",         "type": "artist", "id": 53449,   "tier": "A"},
    {"name": "John Coltrane",       "type": "artist", "id": 24736,   "tier": "A"},
    {"name": "Bill Evans",          "type": "artist", "id": 65463,   "tier": "A"},
    {"name": "Thelonious Monk",     "type": "artist", "id": 34429,   "tier": "A"},
    {"name": "Charles Mingus",      "type": "artist", "id": 39879,   "tier": "A"},
    {"name": "Herbie Hancock",      "type": "artist", "id": 31867,   "tier": "A"},
    {"name": "Sonny Rollins",       "type": "artist", "id": 36797,   "tier": "A"},
    {"name": "Wes Montgomery",      "type": "artist", "id": 53536,   "tier": "A"},

    # ── TIER A — Rock UK Originale ──────────────────────
    # UK pressings anni '60-'70 valgono molto di più delle edizioni US
    {"name": "The Beatles",         "type": "artist", "id": 82730,   "tier": "A"},
    {"name": "Pink Floyd",          "type": "artist", "id": 45467,   "tier": "A"},
    {"name": "Led Zeppelin",        "type": "artist", "id": 3648,    "tier": "A"},
    {"name": "David Bowie",         "type": "artist", "id": 59486,   "tier": "A"},
    {"name": "The Rolling Stones",  "type": "artist", "id": 38216,   "tier": "A"},
    {"name": "The Who",             "type": "artist", "id": 23996,   "tier": "A"},
    {"name": "Jimi Hendrix",        "type": "artist", "id": 27227,   "tier": "A"},
    {"name": "Cream",               "type": "artist", "id": 92803,   "tier": "A"},

    # ── TIER A — Soul / Funk ────────────────────────────
    # Piccole label soul sono spesso rare e sottovalutate
    {"name": "Marvin Gaye",         "type": "artist", "id": 54131,   "tier": "A"},
    {"name": "James Brown",         "type": "artist", "id": 15234,   "tier": "A"},
    {"name": "Curtis Mayfield",     "type": "artist", "id": 75900,   "tier": "A"},
    {"name": "Stevie Wonder",       "type": "artist", "id": 180,     "tier": "A"},
    {"name": "Al Green",            "type": "artist", "id": 119639,  "tier": "A"},
    {"name": "Sly and The Family Stone", "type": "artist", "id": 139858, "tier": "A"},

    # ── TIER B — Hip-Hop Originale ──────────────────────
    # Prime pressature hip-hop anni '88-'98 sempre in forte domanda
    {"name": "Wu-Tang Clan",        "type": "artist", "id": 63791,   "tier": "B"},
    {"name": "Notorious B.I.G.",    "type": "artist", "id": 51478,   "tier": "B"},
    {"name": "Nas",                 "type": "artist", "id": 35783,   "tier": "B"},
    {"name": "Jay-Z",               "type": "artist", "id": 169705,  "tier": "B"},
    {"name": "A Tribe Called Quest","type": "artist", "id": 26759,   "tier": "B"},
    {"name": "De La Soul",          "type": "artist", "id": 66836,   "tier": "B"},
    {"name": "Kendrick Lamar",      "type": "artist", "id": 2874688, "tier": "B"},
    {"name": "Madlib",              "type": "artist", "id": 179820,  "tier": "B"},

    # ── TIER B — Punk / Post-Punk ────────────────────────
    {"name": "The Clash",           "type": "artist", "id": 43511,   "tier": "B"},
    {"name": "Sex Pistols",         "type": "artist", "id": 40603,   "tier": "B"},
    {"name": "Joy Division",        "type": "artist", "id": 68874,   "tier": "B"},
    {"name": "The Smiths",          "type": "artist", "id": 44818,   "tier": "B"},
    {"name": "The Cure",            "type": "artist", "id": 61094,   "tier": "B"},
    {"name": "New Order",           "type": "artist", "id": 15273,   "tier": "B"},

    # ── TIER B — Elettronica Classica ───────────────────
    {"name": "Daft Punk",           "type": "artist", "id": 5765,    "tier": "B"},
    {"name": "Aphex Twin",          "type": "artist", "id": 45,      "tier": "B"},
    {"name": "Boards of Canada",    "type": "artist", "id": 21942,   "tier": "B"},

    # ── TIER B — Ricerche Per Tipo Pressatura ────────────
    # Pressature giapponesi con OBI strip originale
    {
        "name":  "Japan OBI Strip First Press",
        "type":  "search",
        "query": "japan obi strip original pressing",
        "tier":  "B"
    },
    # Edizioni limitate colorate sottovalutate
    {
        "name":  "Colored Vinyl Limited",
        "type":  "search",
        "query": "colored vinyl limited edition 2018 2019 2020",
        "tier":  "B"
    },

    # ── TIER C — Aggiungi i tuoi artisti target ──────────
    # Modifica questa sezione in base al tuo mercato specifico
    {"name": "Nirvana",             "type": "artist", "id": 125246,  "tier": "C"},
    {"name": "Radiohead",           "type": "artist", "id": 3840,    "tier": "C"},
    {"name": "Nick Cave",           "type": "artist", "id": 9747,    "tier": "C"},
    {"name": "Tom Waits",           "type": "artist", "id": 168279,  "tier": "C"},
    {"name": "Bob Dylan",           "type": "artist", "id": 6059,    "tier": "C"},
    {"name": "Neil Young",          "type": "artist", "id": 76896,   "tier": "C"},

]

# ─────────────────────────────────────────────
# KEYWORDS: segnali di rarità nel testo del listing
# Se trovate nella descrizione del venditore, aumentano lo score
# ─────────────────────────────────────────────
RARITY_KEYWORDS = [
    # First press markers
    "first press", "first pressing", "1st press", "1st pressing",
    "original press", "original pressing", "original uk", "original us",
    "original german", "original japan",
    # Pressature speciali
    "obi strip", "obi-strip", "obi", "bowing strip",
    "promo", "white label promo", "dj copy", "not for sale",
    "test press", "test pressing", "acetate",
    # Edizioni limitate
    "numbered", "hand numbered", "hand-numbered", "limited edition",
    "limited to", "limited run", "one-time press",
    # Vinile speciale
    "colored vinyl", "colour vinyl", "red vinyl", "blue vinyl",
    "white vinyl", "clear vinyl", "splatter", "marbled", "picture disc",
    "picture disk",
    # Condizione eccezionale
    "sealed", "still sealed", "factory sealed", "shrink wrap intact",
    "unplayed", "mint unplayed",
    # Errori/varianti
    "misprint", "mispress", "mispressing", "alternate cover",
    "withdrawn", "banned cover", "recalled",
    # Gatefold / inserti originali
    "gatefold original", "poster intact", "all inserts", "original inner",
]

# ─────────────────────────────────────────────
# RED FLAGS: segnali che indicano ristampa o problema
# Penalizzano lo score o scartano il listing
# ─────────────────────────────────────────────
RED_FLAGS = [
    # Label di ristampe moderne note
    "music on vinyl", "back to black", "vinyl me please",
    "rhino records", "demon records", "culture factory",
    "wax love", "speakers corner",
    # Indicatori di ristampa
    "reissue", "re-issue", "repress", "re-press", "re press",
    "remastered", "re-mastered", "digitally remastered",
    "from digital source", "from cd master",
    "180g reissue", "180 gram reissue",
    "anniversary edition" , "commemorative edition",
    # Indicatori specifici nel matrix
    "lacquer cut from digital",
]

# ─────────────────────────────────────────────
# MOLTIPLICATORI PAESE
# Le pressature originali di certi paesi valgono di più
# ─────────────────────────────────────────────
COUNTRY_VALUE_MULTIPLIERS = {
    "Japan":          1.50,   # Pressature giapponesi con OBI = premium
    "UK":             1.30,   # UK press spesso originali e superiori
    "Germany":        1.20,   # Ottime pressature tecnicamente
    "Netherlands":    1.10,   # Philips / Phonogram di qualità
    "France":         1.05,
    "US":             1.00,   # Reference standard
    "Italy":          0.90,
    "Australia":      0.85,
    "Canada":         0.90,
    "Spain":          0.80,
}
