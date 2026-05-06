"""
Telegram Alerts v5
- Primo link: listing Discogs diretto (prezzo verificato OAuth)
- Altri link: eBay IT, eBay UK, Vinted, Wallapop, Subito, Catawiki
- Secondo link fisso: scheda disco su Discogs
"""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from search_links import get_buy_links_message, get_discogs_release_url


def _send(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️  Token Telegram mancanti")
        return False
    url = f"https://api.telegram.org/bot{str(TELEGRAM_BOT_TOKEN).strip()}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":                  str(TELEGRAM_CHAT_ID).strip(),
            "text":                     text[:4096],
            "parse_mode":               "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)
        if r.status_code == 200:
            return True
        data = r.json()
        desc = data.get("description", "")
        if "chat not found" in desc:
            print("  ❌ Telegram: scrivi /start al bot prima di usarlo")
        else:
            print(f"  ❌ Telegram {r.status_code}: {desc}")
        return False
    except Exception as e:
        print(f"  ❌ Telegram exception: {e}")
        return False


def _bar(score: float) -> str:
    try:
        f = max(0, min(10, round(float(score))))
        return "🟩" * f + "⬜" * (10 - f)
    except Exception:
        return "⬜" * 10


def _roi_emoji(roi: float) -> str:
    if roi >= 1.00: return "🚀"
    if roi >= 0.75: return "🔥"
    if roi >= 0.50: return "💰"
    return "✅"


def send_opportunity_alert(opp: dict) -> bool:
    try:
        score = float(opp.get("score", 0) or 0)
        roi   = float(opp.get("roi", 0) or 0)
        lp    = float(opp.get("listing_price", 0) or 0)
        med   = float(opp.get("median_price", 0) or 0)
        est   = float(opp.get("est_sell_price", 0) or 0)
        net   = float(opp.get("gross_profit", 0) or 0)
        want  = int(opp.get("wantlist_count", 0) or 0)
        sale  = int(opp.get("num_for_sale", 0) or 0)

        artist     = opp.get("artist", "?") or "?"
        title      = opp.get("title", "?") or "?"
        release_id = str(opp.get("release_id", "") or "")

        rarity = opp.get("rarity_signals") or []
        flags  = opp.get("red_flags") or []
        rarity_str = "\n".join(f"  ✨ {s}" for s in rarity[:5]) if rarity else "  —"
        flags_str  = "\n".join(f"  ⚠️ {f}" for f in flags[:3])  if flags  else "  —"

        # Link acquisto diretto Discogs (OAuth, prezzo reale)
        discogs_listing = opp.get("listing_url", "") or ""
        # Link scheda disco
        release_url = (
            opp.get("release_url", "")
            or get_discogs_release_url(release_id)
        )

        # Sezione link multi-piattaforma
        links_section = get_buy_links_message(
            artist=artist,
            title=title,
            release_id=release_id,
            discogs_listing_url=discogs_listing,
        )

        seller = opp.get("seller_username", "") or ""
        seller_str = f"👤 Venditore: {seller}\n" if seller and seller != "vedi link" else ""

        msg = (
            f"🎵 <b>VINYL ARBITRAGE ALERT</b>\n\n"
            f"🎯 <b>Score {score:.1f}/10</b>  {_bar(score)}\n\n"
            f"<b>💿 {artist} — {title}</b>\n"
            f"🏷  {opp.get('label','?')} · {opp.get('year','?')} · {opp.get('country','?')}\n"
            f"📀 Condizione: {opp.get('condition','?')}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💸 <b>ECONOMIA (prezzi reali Discogs)</b>\n"
            f"• Prezzo listing:   <b>€{lp:.2f}</b>\n"
            f"• Mediana Discogs:  €{med:.2f}\n"
            f"• Rivendi stimato:  €{est:.2f}\n"
            f"• Profitto netto:   <b>€{net:.2f}</b>\n"
            f"• ROI:             {_roi_emoji(roi)} <b>{roi*100:.0f}%</b>\n"
            f"  (dopo fee 11% + spedizioni)\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 <b>MERCATO</b>\n"
            f"• Wantlist: {want:,}  |  In vendita: {sale}\n"
            f"{seller_str}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✨ <b>RARITÀ</b>\n{rarity_str}\n\n"
            f"⛔ <b>RED FLAGS</b>\n{flags_str}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"{links_section}\n\n"
            f"📖 <a href=\"{release_url}\">Scheda disco su Discogs</a>\n"
            f"━━━━━━━━━━━━━━━━"
        )

        return _send(msg)

    except Exception as e:
        print(f"  Errore build alert: {e}")
        return False


def send_daily_summary(stats: dict) -> bool:
    try:
        msg = (
            f"📊 <b>Vinyl Scanner — Riassunto</b>\n\n"
            f"🔍 Analizzati: {stats.get('scanned', 0):,}\n"
            f"⚡ Trovati:    {stats.get('today_found', 0)}\n"
            f"📱 Alert:      {stats.get('today_alerted', 0)}\n\n"
            f"💰 Profitto storico: €{float(stats.get('total_profit_eur', 0)):.2f}\n"
            f"📦 Acquisti totali:  {stats.get('total_purchases', 0)}"
        )
        return _send(msg)
    except Exception as e:
        print(f"  Errore summary: {e}")
        return False


def send_error_alert(error_msg: str) -> bool:
    try:
        return _send(f"❌ <b>SCANNER ERROR</b>\n<code>{str(error_msg)[:400]}</code>")
    except Exception:
        return False


def send_startup_message() -> bool:
    try:
        import discogs_client as dc
        mode = "OAuth 🔐 (prezzi reali)" if dc.HAS_OAUTH else "Token semplice ⚠️"
    except Exception:
        mode = "?"
    return _send(f"🚀 <b>Vinyl Scanner v8 avviato</b>\nModalità: {mode}")
