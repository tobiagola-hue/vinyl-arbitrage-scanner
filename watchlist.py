import random

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
    # Pressature rare per caratteristiche specifiche
    {"name": "Blue Note Lexington",   "query": "blue note lexington avenue pressing vinyl"},
    {"name": "Beatles Butcher Cover", "query": "beatles butcher cover yesterday today vinyl"},
    {"name": "Led Zep Turquoise",     "query": "led zeppelin turquoise letters vinyl original"},
    {"name": "Dylan Freewheelin Alt", "query": "bob dylan freewheelin withdrawn tracks vinyl"},
    {"name": "Dark Side Misprint",    "query": "pink floyd dark side moon misprint vinyl"},
    {"name": "Van Morrison Astral",   "query": "van morrison astral weeks original vinyl"},
    {"name": "Velvet Underground Peel", "query": "velvet underground peel slowly banana vinyl"},
    {"name": "Massive Attack Mono",   "query": "massive attack mezzanine vinyl"},
    {"name": "Talking Heads Fear",    "query": "talking heads fear of music original vinyl"},
    {"name": "Joni Mitchell Original","query": "joni mitchell original pressing vinyl"},
    {"name": "Captain Beefheart",     "query": "captain beefheart trout mask original vinyl"},
    {"name": "Faust Original",        "query": "faust original german pressing vinyl"},
    {"name": "Can Original",          "query": "can original spoon records vinyl"},
    {"name": "Neu! Original",         "query": "neu original brain records vinyl"},
]

_MIDVALUE_BASE = [
    {"name": "Pink Floyd",         "query": "pink floyd vinyl",         "artist": "Pink Floyd"},
    {"name": "Led Zeppelin",       "query": "led zeppelin vinyl",       "artist": "Led Zeppelin"},
    {"name": "Rolling Stones",     "query": "rolling stones vinyl",     "artist": "Rolling Stones"},
    {"name": "David Bowie",        "query": "david bowie vinyl",        "artist": "David Bowie"},
    {"name": "The Beatles",        "query": "beatles vinyl",            "artist": "Beatles"},
    {"name": "Jimi Hendrix",       "query": "jimi hendrix vinyl",       "artist": "Jimi Hendrix"},
    {"name": "The Doors",          "query": "the doors vinyl",          "artist": "The Doors"},
    {"name": "Bob Dylan",          "query": "bob dylan vinyl",          "artist": "Bob Dylan"},
    {"name": "Neil Young",         "query": "neil young vinyl",         "artist": "Neil Young"},
    {"name": "Fleetwood Mac",      "query": "fleetwood mac vinyl",      "artist": "Fleetwood Mac"},
    {"name": "Nirvana",            "query": "nirvana vinyl",            "artist": "Nirvana"},
    {"name": "Radiohead",          "query": "radiohead vinyl",          "artist": "Radiohead"},
    {"name": "Oasis",              "query": "oasis vinyl",              "artist": "Oasis"},
    {"name": "The Smiths",         "query": "the smiths vinyl",         "artist": "The Smiths"},
    {"name": "The Cure",           "query": "the cure vinyl",           "artist": "The Cure"},
    {"name": "Joy Division",       "query": "joy division vinyl",       "artist": "Joy Division"},
    {"name": "New Order",          "query": "new order vinyl",          "artist": "New Order"},
    {"name": "The Clash",          "query": "the clash vinyl",          "artist": "The Clash"},
    {"name": "Pearl Jam",          "query": "pearl jam vinyl",          "artist": "Pearl Jam"},
    {"name": "Soundgarden",        "query": "soundgarden vinyl",        "artist": "Soundgarden"},
    {"name": "Pixies",             "query": "pixies vinyl",             "artist": "Pixies"},
    {"name": "Daft Punk",          "query": "daft punk vinyl",          "artist": "Daft Punk"},
    {"name": "Aphex Twin",         "query": "aphex twin vinyl",         "artist": "Aphex Twin"},
    {"name": "Boards of Canada",   "query": "boards of canada vinyl",   "artist": "Boards of Canada"},
    {"name": "Chemical Brothers",  "query": "chemical brothers vinyl",  "artist": "Chemical Brothers"},
    {"name": "Kendrick Lamar",     "query": "kendrick lamar vinyl",     "artist": "Kendrick Lamar"},
    {"name": "Frank Ocean",        "query": "frank ocean vinyl",        "artist": "Frank Ocean"},
    {"name": "Tyler The Creator",  "query": "tyler the creator vinyl",  "artist": "Tyler The Creator"},
    {"name": "Mac Miller",         "query": "mac miller vinyl",         "artist": "Mac Miller"},
    {"name": "Madlib",             "query": "madlib vinyl",             "artist": "Madlib"},
    {"name": "Miles Davis",        "query": "miles davis vinyl",        "artist": "Miles Davis"},
    {"name": "John Coltrane",      "query": "john coltrane vinyl",      "artist": "John Coltrane"},
    {"name": "Bill Evans",         "query": "bill evans vinyl",         "artist": "Bill Evans"},
    {"name": "Nick Cave",          "query": "nick cave vinyl",          "artist": "Nick Cave"},
    {"name": "Tom Waits",          "query": "tom waits vinyl",          "artist": "Tom Waits"},
    {"name": "Portishead",         "query": "portishead vinyl",         "artist": "Portishead"},
    {"name": "Massive Attack",     "query": "massive attack vinyl",     "artist": "Massive Attack"},
    {"name": "Burial",             "query": "burial vinyl",             "artist": "Burial"},
    {"name": "Four Tet",           "query": "four tet vinyl",           "artist": "Four Tet"},
    {"name": "Flying Lotus",       "query": "flying lotus vinyl",       "artist": "Flying Lotus"},
    {"name": "Arthur Russell",     "query": "arthur russell vinyl",     "artist": "Arthur Russell"},
    {"name": "Scott Walker",       "query": "scott walker vinyl",       "artist": "Scott Walker"},
    {"name": "Nick Drake",         "query": "nick drake vinyl",         "artist": "Nick Drake"},
    {"name": "Broadcast",          "query": "broadcast vinyl",          "artist": "Broadcast"},
    {"name": "Stereolab",          "query": "stereolab vinyl",          "artist": "Stereolab"},
]

_DYNAMIC_QUERIES = [
    {"name": "Limited Edition 2024",    "query": "limited edition vinyl 2024",          "artist": ""},
    {"name": "Colored Vinyl Rare",      "query": "colored vinyl rare limited",           "artist": ""},
    {"name": "Picture Disc Rare",       "query": "picture disc vinyl rare",              "artist": ""},
    {"name": "Numbered Edition",        "query": "numbered edition vinyl limited",        "artist": ""},
    {"name": "Sealed Vintage",          "query": "sealed vintage vinyl original",         "artist": ""},
    {"name": "First Press",             "query": "first pressing vinyl rare",             "artist": ""},
    {"name": "Soul Funk 70s",           "query": "soul funk 70s vinyl original",          "artist": ""},
    {"name": "Italian Prog Rock",       "query": "italian progressive rock vinyl",         "artist": ""},
    {"name": "Cosmic Disco",            "query": "cosmic disco vinyl rare",               "artist": ""},
    {"name": "Trip Hop",                "query": "trip hop vinyl original",               "artist": ""},
    {"name": "Post Rock",               "query": "post rock vinyl original",              "artist": ""},
    {"name": "Ambient Drone",           "query": "ambient drone vinyl rare",              "artist": ""},
    {"name": "RSD 2024",                "query": "record store day 2024 vinyl",           "artist": ""},
    {"name": "RSD 2023",                "query": "record store day 2023 vinyl",           "artist": ""},
    {"name": "Lotto Vinili",            "query": "lotto vinili collezione rara",          "artist": ""},
    {"name": "Collezione Privata",      "query": "collezione privata vinili",             "artist": ""},
    {"name": "Etichetta Indipendente",  "query": "indie label vinyl rare original",       "artist": ""},
    {"name": "Jazz Contemporaneo",      "query": "contemporary jazz vinyl limited",       "artist": ""},
    {"name": "Hip Hop Old School",      "query": "hip hop old school vinyl original",     "artist": ""},
    {"name": "Drum and Bass Rare",      "query": "drum and bass vinyl rare original",     "artist": ""},
    {"name": "Punk Hardcore",           "query": "punk hardcore vinyl original",          "artist": ""},
    {"name": "Shoegaze",                "query": "shoegaze vinyl original",               "artist": ""},
    {"name": "Dream Pop",               "query": "dream pop vinyl rare",                  "artist": ""},
    {"name": "Lo-fi Indie",             "query": "lo-fi indie vinyl",                     "artist": ""},
    {"name": "Funk Raro",               "query": "funk rare original vinyl",              "artist": ""},
]


def get_midvalue_watchlist(max_items=40):
    result = list(_MIDVALUE_BASE)
    random.shuffle(_DYNAMIC_QUERIES)
    result.extend(_DYNAMIC_QUERIES[:max(0, max_items - len(_MIDVALUE_BASE))])
    random.shuffle(result)
    return result[:max_items]


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
    "lexington ave","van gelder","rl cut","porky prime cut","deaf","hot stamper",
    "original label","deep groove","no groove","promo stamp","cutout",
    "three-folded","tri-fold","gatefold original","insert intact","poster",
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

