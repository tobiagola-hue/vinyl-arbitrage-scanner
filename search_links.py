“””
VINYL ARBITRAGE SCANNER — Search Links
Genera link di ricerca su tutti i marketplace di resale.
Non fa scraping — costruisce URL di ricerca precisi per ogni piattaforma.
“””
import urllib.parse

def _encode(text: str) -> str:
return urllib.parse.quote_plus(str(text or “”))

def build_all_links(artist: str, title: str, release_id: str = “”) -> dict:
“””
Costruisce link di ricerca/acquisto per ogni piattaforma.
Ritorna dict con nome piattaforma → URL.
“””
query_full  = f”{artist} {title} vinyl”
query_short = f”{artist} {title}”

```
links = {}

# ── Discogs Marketplace (link diretto, prezzi verificati) ──
if release_id:
    links["discogs"] = (
        f"https://www.discogs.com/sell/release/{release_id}"
        f"?status=For+Sale&sort=price%2Casc"
    )

# ── eBay Italia ───────────────────────────────────────────
# Categoria 306 = Records, ordine per prezzo + spedizione
links["ebay_it"] = (
    f"https://www.ebay.it/sch/i.html"
    f"?_nkw={_encode(query_full)}"
    f"&_sacat=306"
    f"&LH_ItemCondition=3000"   # Used
    f"&_sop=15"                  # Ordina per prezzo + spedizione
    f"&LH_PrefLoc=3"            # Spedisce in Italia
)

# ── eBay UK (molto più fornito per vinili rari) ───────────
links["ebay_uk"] = (
    f"https://www.ebay.co.uk/sch/i.html"
    f"?_nkw={_encode(query_full)}"
    f"&_sacat=306"
    f"&LH_ItemCondition=3000"
    f"&_sop=15"
)

# ── Vinted Italia ────────────────────────────────────────
links["vinted"] = (
    f"https://www.vinted.it/catalog"
    f"?search_text={_encode(query_short)}"
    f"&catalog_ids=32"  # Categoria musica/CD/vinili
)

# ── Wallapop (spedisce in Italia dall'Europa) ─────────────
links["wallapop"] = (
    f"https://it.wallapop.com/app/search"
    f"?keywords={_encode(query_short)}"
    f"&category_ids=12465"  # Categoria musica
)

# ── Subito.it ─────────────────────────────────────────────
links["subito"] = (
    f"https://www.subito.it/annunci-italia/vendita/usato/"
    f"?q={_encode(query_short)}"
    f"&c=27"  # Categoria musica
)

# ── Catawiki (aste europee) ───────────────────────────────
links["catawiki"] = (
    f"https://www.catawiki.com/en/l/music"
    f"?q={_encode(query_short)}"
)

# ── Mercatino Musicale ────────────────────────────────────
links["mercatino"] = (
    f"https://www.mercatinomusic.it/usato/"
    f"?q={_encode(query_short)}"
)

return links
```

def get_buy_links_message(artist: str, title: str,
release_id: str = “”,
discogs_listing_url: str = “”) -> str:
“””
Costruisce la sezione link del messaggio Telegram.
“””
links = build_all_links(artist, title, release_id)

```
# Se abbiamo il link diretto al listing Discogs, sovrascrive quello generico
if discogs_listing_url:
    links["discogs_direct"] = discogs_listing_url

lines = ["🛒 <b>CERCA E COMPRA</b>\n"]

# Link diretto listing Discogs (prezzo verificato)
if discogs_listing_url:
    lines.append(f"💚 <a href=\"{discogs_listing_url}\">Discogs — listing verificato</a>")
elif links.get("discogs"):
    lines.append(f"💚 <a href=\"{links['discogs']}\">Discogs Marketplace</a>")

# Altri marketplace
lines.append(f"🟡 <a href=\"{links['ebay_it']}\">eBay Italia</a>")
lines.append(f"🟡 <a href=\"{links['ebay_uk']}\">eBay UK</a> (più fornito)")
lines.append(f"🔵 <a href=\"{links['vinted']}\">Vinted Italia</a>")
lines.append(f"🟠 <a href=\"{links['wallapop']}\">Wallapop</a>")
lines.append(f"🔴 <a href=\"{links['subito']}\">Subito.it</a>")
lines.append(f"⚪ <a href=\"{links['catawiki']}\">Catawiki</a> (aste)")

return "\n".join(lines)
```

def get_discogs_release_url(release_id: str) -> str:
“”“Link scheda disco su Discogs.”””
return f”https://www.discogs.com/release/{release_id}” if release_id else “”