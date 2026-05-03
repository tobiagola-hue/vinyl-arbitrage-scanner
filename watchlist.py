"""
VINYL ARBITRAGE SCANNER — Watchlist v3
Query semplificate: meno parole = più risultati Discogs.
"""

WATCHLIST = [

    # ── TIER A — JAZZ ORIGINALE ──────────────────────────
    {"name": "Blue Note Jazz Original",     "type": "search", "query": "blue note jazz original vinyl",         "tier": "A"},
    {"name": "Prestige Jazz Original",      "type": "search", "query": "prestige jazz original pressing vinyl", "tier": "A"},
    {"name": "Impulse Jazz Original",       "type": "search", "query": "impulse jazz original vinyl",           "tier": "A"},
    {"name": "Riverside Jazz Original",     "type": "search", "query": "riverside jazz vinyl original",         "tier": "A"},
    {"name": "Verve Jazz Original",         "type": "search", "query": "verve records jazz original pressing",  "tier": "A"},
    {"name": "Atlantic Jazz Original",      "type": "search", "query": "atlantic records jazz original vinyl",  "tier": "A"},

    # ── TIER A — SOUL / FUNK ─────────────────────────────
    {"name": "Northern Soul 45rpm",         "type": "search", "query": "northern soul 45 rpm original",        "tier": "A"},
    {"name": "Funk Soul Original",          "type": "search", "query": "funk soul original pressing vinyl",     "tier": "A"},
    {"name": "Motown Original",             "type": "search", "query": "motown original pressing vinyl",        "tier": "A"},

    # ── TIER A — KRAUTROCK ───────────────────────────────
    {"name": "Krautrock Original",          "type": "search", "query": "krautrock german original vinyl",       "tier": "A"},
    {"name": "Kosmische Musik Original",    "type": "search", "query": "kosmische musik original pressing",     "tier": "A"},

    # ── TIER A — PSYCH GARAGE ────────────────────────────
    {"name": "Psych Garage 60s Original",   "type": "search", "query": "psychedelic garage original vinyl",    "tier": "A"},
    {"name": "UK Psych Original",           "type": "search", "query": "uk psychedelic original pressing",     "tier": "A"},

    # ── TIER A — PRESSATURE SPECIALI ─────────────────────
    {"name": "Test Pressing Rare",          "type": "search", "query": "test pressing vinyl rare",             "tier": "A"},
    {"name": "White Label Promo",           "type": "search", "query": "white label promo vinyl",              "tier": "A"},

    # ── TIER B — GIAPPONE ────────────────────────────────
    {"name": "Japan OBI Jazz",              "type": "search", "query": "japan obi jazz vinyl",                 "tier": "B"},
    {"name": "Japan OBI Rock",              "type": "search", "query": "japan obi rock vinyl",                 "tier": "B"},
    {"name": "Japan OBI Soul",              "type": "search", "query": "japan obi soul funk vinyl",            "tier": "B"},

    # ── TIER B — LIBRARY MUSIC ───────────────────────────
    {"name": "Library Music Original",      "type": "search", "query": "library music vinyl rare",             "tier": "B"},
    {"name": "Jazz Fusion Original",        "type": "search", "query": "jazz fusion original pressing vinyl",  "tier": "B"},

    # ── TIER B — ELETTRONICA ─────────────────────────────
    {"name": "Electronic Ambient Original", "type": "search", "query": "electronic ambient original vinyl",    "tier": "B"},
    {"name": "Early Techno House Original", "type": "search", "query": "techno house original pressing vinyl", "tier": "B"},

    # ── TIER B — ALTRI GENERI ────────────────────────────
    {"name": "Folk Psych Original",         "type": "search", "query": "folk psych original vinyl",            "tier": "B"},
    {"name": "Reggae Dub Jamaica",          "type": "search", "query": "reggae dub jamaica original vinyl",    "tier": "B"},
    {"name": "Bossa Nova Latin Original",   "type": "search", "query": "bossa nova latin original vinyl",      "tier": "B"},
    {"name": "Hip Hop Original 88-93",      "type": "search", "query": "hip hop original pressing vinyl",      "tier": "B"},

    # ── TIER B — COLORED / LIMITED ───────────────────────
    {"name": "Colored Vinyl Limited",       "type": "search", "query": "colored vinyl limited original",       "tier": "B"},
    {"name": "Picture Disc Original",       "type": "search", "query": "picture disc original vinyl",          "tier": "B"},

    # ── TIER C ───────────────────────────────────────────
    {"name": "Post Punk Original",          "type": "search", "query": "post punk original pressing vinyl",    "tier": "C"},
    {"name": "Prog Rock Original",          "type": "search", "query": "progressive rock original vinyl",      "tier": "C"},
    {"name": "Ambient Drone Original",      "type": "search", "query": "ambient drone original pressing",      "tier": "C"},
]

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
