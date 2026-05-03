"""
VINYL ARBITRAGE SCANNER — Watchlist v2
Focus su: pressature rare, label di nicchia, generi cult.
NON artisti mainstream famosi (troppa competizione, margini bassi).
Strategia: cercare per GENERE + TIPO PRESSATURA + LABEL piccola.
"""

WATCHLIST = [

    # ── JAZZ ORIGINALE ANNI '50-'60 ─────────────────────
    {"name": "Blue Note Original Press",    "type": "search", "query": "blue note original pressing 1950s 1960s", "tier": "A"},
    {"name": "Prestige Records Original",   "type": "search", "query": "prestige records original pressing jazz vinyl", "tier": "A"},
    {"name": "Impulse Records Original",    "type": "search", "query": "impulse records original pressing vinyl", "tier": "A"},
    {"name": "Riverside Records Jazz",      "type": "search", "query": "riverside records original jazz pressing vinyl", "tier": "A"},

    # ── SOUL / FUNK ──────────────────────────────────────
    {"name": "Northern Soul 45",            "type": "search", "query": "northern soul original 45 rpm rare", "tier": "A"},
    {"name": "Funk Soul Small Label",       "type": "search", "query": "funk soul rare small label original 1960s 1970s", "tier": "A"},
    {"name": "Motown Original",             "type": "search", "query": "motown tamla original pressing 1960s vinyl", "tier": "A"},

    # ── KRAUTROCK / PROG TEDESCO ─────────────────────────
    {"name": "Krautrock Original German",   "type": "search", "query": "krautrock original german pressing 1970s vinyl", "tier": "A"},
    {"name": "Can Faust Neu Original",      "type": "search", "query": "can faust neu amon duul original pressing vinyl", "tier": "A"},

    # ── PSYCH / GARAGE '60s ──────────────────────────────
    {"name": "Psych Garage 60s",            "type": "search", "query": "psychedelic garage original pressing 1966 1967 1968", "tier": "A"},
    {"name": "UK Psych Original",           "type": "search", "query": "uk psychedelic original pressing vinyl 1967 1968 1969", "tier": "A"},

    # ── LIBRARY MUSIC ────────────────────────────────────
    {"name": "Library Music Rare",          "type": "search", "query": "library music original pressing vinyl rare", "tier": "B"},
    {"name": "Jazz Fusion Rare",            "type": "search", "query": "jazz fusion rare original pressing 1970s vinyl", "tier": "B"},

    # ── PRESSATURE GIAPPONESI CON OBI ───────────────────
    {"name": "Japan OBI Jazz",              "type": "search", "query": "japan obi strip jazz vinyl", "tier": "B"},
    {"name": "Japan OBI Rock",              "type": "search", "query": "japan obi strip rock vinyl original", "tier": "B"},

    # ── ELETTRONICA ANNI '70-'90 ─────────────────────────
    {"name": "Electronic Ambient 70s-80s",  "type": "search", "query": "electronic ambient original pressing vinyl 1970s 1980s", "tier": "B"},
    {"name": "Early Techno House 88-91",    "type": "search", "query": "early techno house original pressing 1988 1989 1990 1991", "tier": "B"},

    # ── FOLK / PSYCH-FOLK ────────────────────────────────
    {"name": "Folk Psych Original",         "type": "search", "query": "folk psych original pressing vinyl 1968 1969 1970 1971", "tier": "B"},

    # ── REGGAE / DUB ORIGINALE ───────────────────────────
    {"name": "Reggae Dub Jamaica Original", "type": "search", "query": "reggae dub original jamaican pressing vinyl studio one", "tier": "B"},

    # ── LATIN / BOSSA NOVA ───────────────────────────────
    {"name": "Bossa Nova Latin Original",   "type": "search", "query": "bossa nova latin original pressing vinyl 1960s rare", "tier": "B"},

    # ── TIPO PRESSATURA SPECIALE ─────────────────────────
    {"name": "Test Press Acetate",          "type": "search", "query": "test pressing acetate vinyl rare", "tier": "A"},
    {"name": "White Label Promo",           "type": "search", "query": "white label promo original vinyl not for sale", "tier": "A"},
    {"name": "Colored Vinyl Limited",       "type": "search", "query": "colored vinyl limited edition original rare", "tier": "B"},

    # ── HIP HOP ORIGINALE '88-'93 ────────────────────────
    {"name": "Hip Hop Original 88-93",      "type": "search", "query": "hip hop original pressing vinyl 1988 1989 1990 1991 1992 1993", "tier": "B"},

    # ── POST-PUNK / COLD WAVE ────────────────────────────
    {"name": "Post Punk Cold Wave 79-82",   "type": "search", "query": "post punk cold wave original pressing 1979 1980 1981 1982", "tier": "C"},

    # ── PROG ROCK ORIGINALE ──────────────────────────────
    {"name": "Prog Rock Original 70s",      "type": "search", "query": "progressive rock original pressing vinyl 1970 1971 1972 1973", "tier": "C"},
]

# ─────────────────────────────────────────────
# KEYWORDS RARITÀ
# ─────────────────────────────────────────────
RARITY_KEYWORDS = [
    "first press", "first pressing", "1st press", "1st pressing",
    "original press", "original pressing", "original uk", "original us",
    "original german", "original japan", "original french",
    "obi strip", "obi-strip", "obi",
    "promo", "white label promo", "dj copy", "not for sale",
    "test press", "test pressing", "acetate",
    "numbered", "hand numbered", "limited edition", "limited to",
    "one-time press",
    "colored vinyl", "colour vinyl", "red vinyl", "blue vinyl",
    "white vinyl", "clear vinyl", "splatter", "marbled", "picture disc",
    "sealed", "still sealed", "factory sealed", "unplayed",
    "misprint", "mispress", "alternate cover", "withdrawn", "banned",
    "gatefold original", "poster intact", "all inserts",
    "matrix", "dead wax", "runout",
]

# ─────────────────────────────────────────────
# RED FLAGS: ristampe moderne
# ─────────────────────────────────────────────
RED_FLAGS = [
    "music on vinyl", "back to black", "vinyl me please",
    "rhino records", "demon records", "culture factory",
    "wax love", "speakers corner", "friday music",
    "reissue", "re-issue", "repress", "re-press",
    "remastered", "digitally remastered",
    "from digital source", "from cd master",
    "180g reissue", "anniversary edition",
    "lacquer cut from digital",
]

# ─────────────────────────────────────────────
# MOLTIPLICATORI PAESE
# ─────────────────────────────────────────────
COUNTRY_VALUE_MULTIPLIERS = {
    "Japan":       1.50,
    "UK":          1.30,
    "Germany":     1.20,
    "Netherlands": 1.10,
    "France":      1.05,
    "US":          1.00,
    "Italy":       0.90,
    "Australia":   0.85,
    "Canada":      0.90,
    "Spain":       0.80,
}
