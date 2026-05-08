"""
Telegram Alerts v6 — Alert singoli + Recap giornalieri.
"""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from search_links import get_buy_links_message, get_discogs_release_url


def _send(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  Token Telegram mancanti")
        return False
    url = f"https://api.telegram.org/bot{str(TELEGRAM_BOT_TOKEN).strip()}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": str(TELEGRAM_CHAT_ID).strip(),
            "text": text[:4096],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)
        if r.status_code == 200:
            return True
        desc = r.json().get("description", "")
        print(f"  Telegram {r.status_code}: {desc}")
        return False
    except Exception as e:
        print(f"  Telegram exception: {e}")
        return False


def _bar(score):
    try:
        f = max(0, min(10, round(float(score))))
        return "🟩" * f + "⬜" * (10 - f)
    except Exception:
        return "⬜" * 10


def _roi_emoji(roi):
    if roi >= 1.00: return "🚀"
    if roi >= 0.75: return "🔥"
    if roi >= 0.50: return "💰"
    return "✅"


def send_opportunity_alert(opp: dict) -> bool:
    try:
        score  = float(opp.get("score", 0) or 0)
        roi    = float(opp.get("roi", 0) or 0)
        lp     = float(opp.get("listing_price", 0) or 0)
        med    = float(opp.get("median_price", 0) or 0)
        est    = float(opp.get("est_sell_price", 0) or 0)
        net    = float(opp.get("gross_profit", 0) or 0)
        want   = int(opp.get("wantlist_count", 0) or 0)
        sale   = int(opp.get("num_for_sale", 0) or 0)
        artist = opp.get("artist", "?") or "?"
        title  = opp.get("title", "?") or "?"
        mode   = opp.get("mode", "expensive")
        rid    = str(opp.get("release_id", "") or "")

        rarity = opp.get("rarity_signals") or []
        flags  = opp.get("red_flags") or []
        rarity_str = "\n".join(f"  ✨ {s}" for s in rarity[:4]) if rarity else "  —"
        flags_str  = "\n".join(f"  ⚠️ {f}" for f in flags[:3])  if flags  else "  —"

        buy_url     = opp.get("listing_url", "") or ""
        release_url = opp.get("release_url", "") or get_discogs_release_url(rid)

        mode_label = "💎 ALTO VALORE" if mode == "expensive" else "🎯 MEDIO VALORE"
        links_section = get_buy_links_message(artist, title, rid, buy_url)
        seller = opp.get("seller_username", "") or ""
        seller_str = f"👤 Venditore: {seller}\n" if seller and seller != "vedi link" else ""

        msg = (
            f"🎵 <b>VINYL ARBITRAGE — {mode_label}</b>\n\n"
            f"🎯 <b>Score {score:.1f}/10</b>  {_bar(score)}\n\n"
            f"<b>💿 {artist} — {title}</b>\n"
            f"🏷  {opp.get('label','?')} · {opp.get('year','?')} · {opp.get('country','?')}\n"
            f"📀 Condizione: {opp.get('condition','?')}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💸 <b>ECONOMIA</b>\n"
            f"• Prezzo listing:   <b>€{lp:.2f}</b>\n"
            f"• Mediana Discogs:  €{med:.2f}\n"
            f"• Rivendi stimato:  €{est:.2f}\n"
            f"• Profitto netto:   <b>€{net:.2f}</b>\n"
            f"• ROI:             {_roi_emoji(roi)} <b>{roi*100:.0f}%</b>\n\n"
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
        print(f"  Errore alert: {e}")
        return False


def send_recap_expensive(opportunities: list):
    """Recap ore 7:00 — Top 3 vinili alto valore."""
    if not opportunities:
        return _send("📊 <b>Recap 7:00 — Alto Valore</b>\n\nNessuna opportunità nelle ultime 24h.")

    msg = "☀️ <b>RECAP 7:00 — TOP 3 ALTO VALORE</b>\n"
    msg += "Migliori opportunità delle ultime 24h\n\n"

    for i, opp in enumerate(opportunities[:3], 1):
        roi = float(opp.get("roi", 0) or 0)
        net = float(opp.get("gross_profit", 0) or 0)
        lp  = float(opp.get("listing_price", 0) or 0)
        med = float(opp.get("median_price", 0) or 0)
        buy = opp.get("listing_url", "") or ""
        rel = opp.get("release_url", "") or ""

        msg += f"{'🥇' if i==1 else '🥈' if i==2 else '🥉'} "
        msg += f"<b>{opp.get('artist','?')} — {opp.get('title','?')}</b>\n"
        msg += f"   €{lp:.0f} → €{med:.0f} | ROI {roi*100:.0f}% | +€{net:.0f}\n"
        if buy:
            msg += f"   🛒 <a href=\"{buy}\">Compra ora</a>"
        if rel:
            msg += f" · 📖 <a href=\"{rel}\">Discogs</a>"
        msg += "\n\n"

    return _send(msg)


def send_recap_midvalue(opportunities: list, slot: str = "13:00"):
    """Recap ore 13:00 e 18:00 — Top 10 vinili medio valore."""
    if not opportunities:
        return _send(
            f"📊 <b>Recap {slot} — Medio Valore</b>\n\n"
            f"Nessuna opportunità nelle ultime 24h."
        )

    emoji_slot = "🌞" if slot == "13:00" else "🌆"
    msg = f"{emoji_slot} <b>RECAP {slot} — TOP 10 MEDIO VALORE</b>\n"
    msg += "Ordinati per vantaggio economico\n\n"

    for i, opp in enumerate(opportunities[:10], 1):
        roi = float(opp.get("roi", 0) or 0)
        net = float(opp.get("gross_profit", 0) or 0)
        lp  = float(opp.get("listing_price", 0) or 0)
        buy = opp.get("listing_url", "") or ""
        rel = opp.get("release_url", "") or ""

        msg += f"{i}. <b>{opp.get('artist','?')} — {opp.get('title','?')}</b>\n"
        msg += f"   €{lp:.0f} · ROI {roi*100:.0f}% · +€{net:.0f}\n"
        if buy:
            msg += f"   🛒 <a href=\"{buy}\">Compra</a>"
        if rel:
            msg += f" · 📖 <a href=\"{rel}\">Discogs</a>"
        msg += "\n\n"

        # Telegram ha limite 4096 caratteri
        if len(msg) > 3500:
            msg += f"... e altri {len(opportunities)-i} risultati"
            break

    return _send(msg)


def send_daily_summary(stats: dict) -> bool:
    try:
        msg = (
            f"📊 <b>Vinyl Scanner — Riassunto run</b>\n\n"
            f"🔍 Analizzati: {stats.get('scanned', 0):,}\n"
            f"⚡ Trovati:    {stats.get('today_found', 0)}\n"
            f"📱 Alert:      {stats.get('today_alerted', 0)}\n\n"
            f"💰 Profitto storico: €{float(stats.get('total_profit_eur', 0)):.2f}"
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


def send_startup_message(mode: str) -> bool:
    try:
        import discogs_client as dc
        auth = "OAuth 🔐" if dc.HAS_OAUTH else "Token ⚠️"
    except Exception:
        auth = "?"
    label = "💎 Alto Valore" if mode == "expensive" else "🎯 Medio Valore"
    return _send(f"🚀 <b>Vinyl Scanner avviato</b>\nModalità: {label} | Auth: {auth}")
