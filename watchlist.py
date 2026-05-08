"""
VINYL ARBITRAGE SCANNER — Watchlist v4
Due livelli: EXPENSIVE (medio-alta fascia) e MIDVALUE (media fascia).
"""

# ─────────────────────────────────────────────────────
# TIER EXPENSIVE — Vinili alto valore (mediana > €50)
# Scanner attivo nelle prime 6 run della giornata
# ─────────────────────────────────────────────────────
WATCHLIST_EXPENSIVE = [
    {"name": "Blue Note Jazz Original",     "query": "blue note jazz original vinyl",         "tier": "A"},
    {"name": "Prestige Jazz Original",      "query": "prestige jazz original pressing vinyl",  "tier": "A"},
    {"name": "Impulse Jazz Original",       "query": "impulse jazz original vinyl",            "tier": "A"},
    {"name": "Riverside Jazz Original",     "query": "riverside jazz vinyl original",          "tier": "A"},
    {"name": "Verve Jazz Original",         "query": "verve records jazz original pressing",   "tier": "A"},
    {"name": "Atlantic Jazz Original",      "query": "atlantic records jazz original vinyl",   "tier": "A"},
    {"name": "Northern Soul 45rpm",         "query": "northern soul original 45 rpm rare",    "tier": "A"},
    {"name": "Krautrock Original German",   "query": "krautrock german original vinyl",        "tier": "A"},
    {"name": "Psych Garage 60s Original",   "query": "psychedelic garage original vinyl",     "tier": "A"},
    {"name": "UK Psych Original",           "query": "uk psychedelic original pressing",      "tier": "A"},
    {"name": "Library Music Rare",          "query": "library music vinyl rare",              "tier": "A"},
    {"name": "Test Pressing Rare",          "query": "test pressing vinyl rare",              "tier": "A"},
    {"name": "Japan OBI Jazz",              "query": "japan obi jazz vinyl",                  "tier": "B"},
    {"name": "Japan OBI Rock",              "query": "japan obi rock vinyl original",         "tier": "B"},
    {"name": "Japan OBI Soul",              "query": "japan obi soul funk vinyl",             "tier": "B"},
    {"name": "Folk Psych Original",         "query": "folk psych original vinyl",             "tier": "B"},
    {"name": "Reggae Dub Jamaica",          "query": "reggae dub jamaica original vinyl",     "tier": "B"},
    {"name": "Hip Hop Original 88-93",      "query": "hip hop original pressing vinyl",       "tier": "B"},
    {"name": "Funk Soul Original",          "query": "funk soul original pressing vinyl",     "tier": "B"},
    {"name": "Motown Original",             "query": "motown original pressing vinyl",        "tier": "B"},
    {"name": "Electronic Ambient 70s-80s",  "query": "electronic ambient original vinyl",     "tier": "B"},
    {"name": "Early Techno House Original", "query": "techno house original pressing vinyl",  "tier": "B"},
    {"name": "White Label Promo",           "query": "white label promo vinyl",               "tier": "B"},
    {"name": "Post Punk Original",          "query": "post punk original pressing vinyl",     "tier": "C"},
    {"name": "Prog Rock Original 70s",      "query": "progressive rock original vinyl",       "tier": "C"},
    {"name": "Ambient Drone Original",      "query": "ambient drone original pressing",       "tier": "C"},
    {"name": "Bossa Nova Latin Original",   "query": "bossa nova latin original vinyl",       "tier": "C"},
    {"name": "Jazz Fusion Original",        "query": "jazz fusion original pressing vinyl",   "tier": "C"},
    {"name": "Kosmische Musik Original",    "query": "kosmische musik original pressing",     "tier": "C"},
    {"name": "Colored Vinyl Limited",       "query": "colored vinyl limited original rare",   "tier": "C"},
]

# ─────────────────────────────────────────────────────
# TIER MIDVALUE — Vinili medio valore (mediana €20-€60)
# Scanner attivo nelle ultime 6 run della giornata
# Cerca buoni dischi a basso prezzo sui siti di resale
# ─────────────────────────────────────────────────────
WATCHLIST_MIDVALUE = [
    # Rock classico
    {"name": "Classic Rock 70s Vinyl",      "query": "classic rock 1970s original vinyl",    "tier": "A"},
    {"name": "Pink Floyd Original",         "query": "pink floyd original pressing vinyl",   "tier": "A"},
    {"name": "Led Zeppelin Original",       "query": "led zeppelin original pressing vinyl", "tier": "A"},
    {"name": "Rolling Stones Original",     "query": "rolling stones original pressing",     "tier": "A"},
    {"name": "David Bowie Original",        "query": "david bowie original pressing vinyl",  "tier": "A"},
    {"name": "Beatles Original UK",         "query": "beatles original uk pressing vinyl",   "tier": "A"},
    # Pop / Indie
    {"name": "Indie Rock 90s Original",     "query": "indie rock 1990s original vinyl",      "tier": "A"},
    {"name": "Nirvana Original Press",      "query": "nirvana original pressing vinyl",      "tier": "A"},
    {"name": "Radiohead Original",          "query": "radiohead original pressing vinyl",    "tier": "A"},
    {"name": "Oasis Original Pressing",     "query": "oasis original pressing vinyl",        "tier": "A"},
    # Elettronica moderna
    {"name": "Daft Punk Vinyl",             "query": "daft punk original vinyl",             "tier": "B"},
    {"name": "Aphex Twin Vinyl",            "query": "aphex twin vinyl",                     "tier": "B"},
    {"name": "Boards of Canada",            "query": "boards of canada vinyl",               "tier": "B"},
    {"name": "Chemical Brothers",           "query": "chemical brothers original vinyl",     "tier": "B"},
    # Hip Hop moderno
    {"name": "Kendrick Lamar Vinyl",        "query": "kendrick lamar vinyl original",        "tier": "B"},
    {"name": "Tyler The Creator Vinyl",     "query": "tyler the creator vinyl",              "tier": "B"},
    {"name": "Frank Ocean Vinyl",           "query": "frank ocean vinyl",                    "tier": "B"},
    {"name": "Mac Miller Vinyl",            "query": "mac miller vinyl",                     "tier": "B"},
    # Jazz moderno / nu-jazz
    {"name": "Madlib Vinyl",                "query": "madlib vinyl original",                "tier": "B"},
    {"name": "Flying Lotus Vinyl",          "query": "flying lotus vinyl",                   "tier": "B"},
    {"name": "Hiatus Kaiyote",              "query": "hiatus kaiyote vinyl",                 "tier": "B"},
    # Record Store Day / Edizioni limitate
    {"name": "Record Store Day 2020-2023",  "query": "record store day vinyl 2020 2021 2022 2023", "tier": "C"},
    {"name": "Limited Edition Numbered",    "query": "limited edition numbered vinyl",       "tier": "C"},
    {"name": "Picture Disc",                "query": "picture disc vinyl original",          "tier": "C"},
    # Rock alternativo / grunge
    {"name": "Pearl Jam Original",          "query": "pearl jam original vinyl",             "tier": "C"},
    {"name": "Soundgarden Original",        "query": "soundgarden original vinyl pressing",  "tier": "C"},
    {"name": "Pixies Original",             "query": "pixies original pressing vinyl",       "tier": "C"},
    {"name": "Smashing Pumpkins",           "query": "smashing pumpkins original vinyl",     "tier": "C"},
    {"name": "Tom Waits Vinyl",             "query": "tom waits vinyl original",             "tier": "C"},
    {"name": "Nick Cave Vinyl",             "query": "nick cave vinyl original pressing",    "tier": "C"},
]

# ─────────────────────────────────────────────────────
# KEYWORDS RARITÀ
# ─────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────
# RED FLAGS
# ─────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────
# MOLTIPLICATORI PAESE
# ─────────────────────────────────────────────────────
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
