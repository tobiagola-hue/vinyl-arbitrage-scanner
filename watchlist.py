"""
VINYL ARBITRAGE SCANNER — Watchlist v5
Watchlist dinamica: cerca in Discogs query variate ogni run.
EXPENSIVE: alto valore, Discogs->Discogs
MIDVALUE: eBay->Discogs, lista ampia e rotante
"""
import random

# ─── EXPENSIVE: Discogs→Discogs (alto valore) ─────────────────
WATCHLIST_EXPENSIVE = [
    {"name": "Blue Note Jazz",        "query": "blue note jazz original vinyl"},
    {"name": "Prestige Jazz",         "query": "prestige jazz original pressing vinyl"},
    {"name": "Impulse Jazz",          "query": "impulse jazz original vinyl"},
    {"name": "Riverside Jazz",        "query": "riverside jazz vinyl original"},
    {"name": "Verve Jazz",            "query": "verve records jazz original pressing"},
    {"name": "Atlantic Jazz",         "query": "atlantic records jazz original vinyl"},
    {"name": "Northern Soul 45",      "query": "northern soul original 45 rpm rare"},
    {"name": "Krautrock Original",    "query": "krautrock german original vinyl"},
    {"name": "Psych Garage 60s",      "query": "psychedelic garage original vinyl"},
    {"name": "UK Psych",              "query": "uk psychedelic original pressing"},
    {"name": "Library Music",         "query": "library music vinyl rare"},
    {"name": "Test Pressing",         "query": "test pressing vinyl rare"},
    {"name": "Japan OBI Jazz",        "query": "japan obi jazz vinyl"},
    {"name": "Japan OBI Rock",        "query": "japan obi rock vinyl original"},
    {"name": "Folk Psych",            "query": "folk psych original vinyl"},
    {"name": "Reggae Dub Jamaica",    "query": "reggae dub jamaica original vinyl"},
    {"name": "Hip Hop 88-93",         "query": "hip hop original pressing vinyl"},
    {"name": "Funk Soul Original",    "query": "funk soul original pressing vinyl"},
    {"name": "Electronic Ambient",    "query": "electronic ambient original vinyl"},
    {"name": "White Label Promo",     "query": "white label promo vinyl"},
    {"name": "Post Punk Original",    "query": "post punk original pressing vinyl"},
    {"name": "Prog Rock 70s",         "query": "progressive rock original vinyl"},
    {"name": "Bossa Nova Latin",      "query": "bossa nova latin original vinyl"},
    {"name": "Jazz Fusion",           "query": "jazz fusion original pressing vinyl"},
    {"name": "Colored Vinyl Limited", "query": "colored vinyl limited original rare"},
]

# ─── MIDVALUE BASE: artisti e release ad alta domanda ─────────
_MIDVALUE_BASE = [
    # Classic Rock
    {"name": "Pink Floyd",          "query": "pink floyd original vinyl",        "artist": "Pink Floyd"},
    {"name": "Led Zeppelin",        "query": "led zeppelin original vinyl",      "artist": "Led Zeppelin"},
    {"name": "Rolling Stones",      "query": "rolling stones original vinyl",    "artist": "Rolling Stones"},
    {"name": "David Bowie",         "query": "david bowie vinyl original",       "artist": "David Bowie"},
    {"name": "The Beatles",         "query": "beatles original vinyl",           "artist": "Beatles"},
    {"name": "Jimi Hendrix",        "query": "jimi hendrix original vinyl",      "artist": "Jimi Hendrix"},
    {"name": "The Doors",           "query": "the doors original vinyl",         "artist": "The Doors"},
    {"name": "Bob Dylan",           "query": "bob dylan original vinyl",         "artist": "Bob Dylan"},
    {"name": "Neil Young",          "query": "neil young original vinyl",        "artist": "Neil Young"},
    {"name": "Fleetwood Mac",       "query": "fleetwood mac original vinyl",     "artist": "Fleetwood Mac"},
    # Alternative/Indie
    {"name": "Nirvana",             "query": "nirvana original vinyl",           "artist": "Nirvana"},
    {"name": "Radiohead",           "query": "radiohead original vinyl",         "artist": "Radiohead"},
    {"name": "Oasis",               "query": "oasis original vinyl",             "artist": "Oasis"},
    {"name": "The Smiths",          "query": "the smiths original vinyl",        "artist": "The Smiths"},
    {"name": "The Cure",            "query": "the cure original vinyl",          "artist": "The Cure"},
    {"name": "Joy Division",        "query": "joy division original vinyl",      "artist": "Joy Division"},
    {"name": "New Order",           "query": "new order original vinyl",         "artist": "New Order"},
    {"name": "The Clash",           "query": "the clash original vinyl",         "artist": "The Clash"},
    {"name": "Pearl Jam",           "query": "pearl jam original vinyl",         "artist": "Pearl Jam"},
    {"name": "Soundgarden",         "query": "soundgarden original vinyl",       "artist": "Soundgarden"},
    {"name": "Pixies",              "query": "pixies original vinyl",            "artist": "Pixies"},
    # Electronic
    {"name": "Daft Punk",           "query": "daft punk original vinyl",         "artist": "Daft Punk"},
    {"name": "Aphex Twin",          "query": "aphex twin vinyl",                 "artist": "Aphex Twin"},
    {"name": "Boards of Canada",    "query": "boards of canada vinyl",           "artist": "Boards of Canada"},
    {"name": "Chemical Brothers",   "query": "chemical brothers vinyl",          "artist": "Chemical Brothers"},
    # Hip Hop
    {"name": "Kendrick Lamar",      "query": "kendrick lamar vinyl",             "artist": "Kendrick Lamar"},
    {"name": "Frank Ocean",         "query": "frank ocean vinyl",                "artist": "Frank Ocean"},
    {"name": "Tyler The Creator",   "query": "tyler the creator vinyl",          "artist": "Tyler The Creator"},
    {"name": "Mac Miller",          "query": "mac miller vinyl",                 "artist": "Mac Miller"},
    {"name": "Madlib",              "query": "madlib vinyl",                     "artist": "Madlib"},
    # Jazz
    {"name": "Miles Davis",         "query": "miles davis vinyl",                "artist": "Miles Davis"},
    {"name": "John Coltrane",       "query": "john coltrane vinyl",              "artist": "John Coltrane"},
    {"name": "Bill Evans",          "query": "bill evans vinyl",                 "artist": "Bill Evans"},
]

# ─── QUERY DINAMICHE: cambiano ad ogni run ─────────────────────
_DYNAMIC_QUERIES = [
    # Limited / speciali
    {"name": "Limited Edition 2023-24", "query": "limited edition vinyl 2023 2024",          "artist": ""},
    {"name": "Colored Vinyl Rare",      "query": "colored vinyl rare limited",               "artist": ""},
    {"name": "Picture Disc Rare",       "query": "picture disc vinyl rare",                  "artist": ""},
    {"name": "Numbered Edition",        "query": "numbered edition vinyl limited",            "artist": ""},
    {"name": "Sealed Vintage",          "query": "sealed vintage vinyl original",             "artist": ""},
    {"name": "First Press Rare",        "query": "first pressing vinyl rare",                "artist": ""},
    # Generi caldi
    {"name": "Soul Funk 70s",           "query": "soul funk 70s vinyl original",             "artist": ""},
    {"name": "Italian Prog Rock",       "query": "italian progressive rock vinyl",            "artist": ""},
    {"name": "Cosmic Disco",            "query": "cosmic disco vinyl rare",                  "artist": ""},
    {"name": "Ambient Drone",           "query": "ambient drone vinyl",                      "artist": ""},
    {"name": "Post Rock",               "query": "post rock vinyl original",                 "artist": ""},
    {"name": "Trip Hop",                "query": "trip hop vinyl original",                  "artist": ""},
    # Record Store Day
    {"name": "RSD Exclusive",           "query": "record store day exclusive vinyl",         "artist": ""},
    {"name": "RSD 2023",                "query": "record store day 2023 vinyl",              "artist": ""},
    {"name": "RSD 2024",                "query": "record store day 2024 vinyl",              "artist": ""},
    # Svendite / svuota cantine
    {"name": "Lotto Vinili",            "query": "lotto vinili collezione",                  "artist": ""},
    {"name": "Collezione Privata",      "query": "collezione privata vinili rari",           "artist": ""},
    # Artisti cult meno noti
    {"name": "Nick Drake",              "query": "nick drake vinyl",                         "artist": "Nick Drake"},
    {"name": "Tom Waits",               "query": "tom waits vinyl original",                 "artist": "Tom Waits"},
    {"name": "Nick Cave",               "query": "nick cave vinyl original",                 "artist": "Nick Cave"},
    {"name": "Scott Walker",            "query": "scott walker vinyl original",              "artist": "Scott Walker"},
    {"name": "Arthur Russell",          "query": "arthur russell vinyl",                     "artist": "Arthur Russell"},
    {"name": "Broadcast",               "query": "broadcast vinyl rare",                     "artist": "Broadcast"},
    {"name": "Stereolab",               "query": "stereolab vinyl rare",                     "artist": "Stereolab"},
    {"name": "Portishead",              "query": "portishead vinyl original",                "artist": "Portishead"},
    {"name": "Massive Attack",          "query": "massive attack vinyl original",            "artist": "Massive Attack"},
    {"name": "Burial",                  "query": "burial vinyl",                             "artist": "Burial"},
    {"name": "Four Tet",                "query": "four tet vinyl",                           "artist": "Four Tet"},
    {"name": "Flying Lotus",            "query": "flying lotus vinyl",                       "artist": "Flying Lotus"},
]


def get_midvalue_watchlist(max_items=30):
    """
    Genera lista dinamica: artisti base + query dinamiche casuali.
    Cambia ogni run per coprire piu territorio.
    """
    # Sempre includi i base
    result = list(_MIDVALUE_BASE)
    # Aggiungi query dinamiche casuali (ruota ad ogni run)
    random.shuffle(_DYNAMIC_QUERIES)
    result.extend(_DYNAMIC_QUERIES[:max(0, max_items - len(_MIDVALUE_BASE))])
    # Mischia per varieta
    random.shuffle(result)
    return result[:max_items]


# Esporta watchlist dinamica
WATCHLIST_MIDVALUE = get_midvalue_watchlist(40)


RARITY_KEYWORDS = [
    "first press","first pressing","1st press","original press","original pressing",
    "original uk","original us","original german","original japan",
    "obi strip","obi-strip","obi","promo","white label promo","not for sale",
    "test press","test pressing","acetate","numbered","hand numbered",
    "limited edition","limited to","colored vinyl","colour vinyl","red vinyl",
    "blue vinyl","white vinyl","clear vinyl","splatter","marbled","picture disc",
    "sealed","still sealed","factory sealed","unplayed","misprint","mispress",
    "alternate cover","withdrawn","banned","gatefold original","matrix","dead wax",
]

RED_FLAGS = [
    "music on vinyl","back to black","vinyl me please","rhino records",
    "demon records","culture factory","wax love","speakers corner",
    "reissue","re-issue","repress","re-press","remastered",
    "digitally remastered","from digital source","180g reissue",
    "anniversary edition","lacquer cut from digital",
]

COUNTRY_VALUE_MULTIPLIERS = {
    "Japan": 1.50, "UK": 1.30, "Germany": 1.20,
    "Netherlands": 1.10, "France": 1.05, "US": 1.00,
    "Italy": 0.90, "Australia": 0.85, "Canada": 0.90, "Spain": 0.80,
}
