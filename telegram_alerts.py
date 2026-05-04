"""
Telegram Alerts v3 — fix "chat not found" con auto-retry e diagnostica.
"""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _send(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        print("  ⚠️  TELEGRAM_BOT_TOKEN mancante")
        return False
    if not TELEGRAM_CHAT_ID:
        print("  ⚠️  TELEGRAM_CHAT_ID mancante")
        return False

    chat_id = str(TELEGRAM_CHAT_ID).strip()
    token   = str(TELEGRAM_BOT_TOKEN).strip()
    url     = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        r = requests.post(url, json={
            "chat_id":                  chat_id,
            "text":                     text[:4096],
            "parse_mode":               "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)

        if r.status_code == 200:
            return True

        data = r.json()
        desc = data.get("description", "")

        if "chat not found" in desc:
            print(f"  ❌ Telegram: chat non trovata.")
            print(f"     → Apri Telegram, cerca @{token.split(':')[1][:10]}... e scrivi /start")
            print(f"     → Oppure verifica che TELEGRAM_CHAT_ID={chat_id} sia corretto")
        else:
            print(f"  ❌ Telegram error {r.status_code}: {desc}")
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
        score      = float(opp.get("score", 0) or 0)
        roi        = float(opp.get("roi", 0) or 0)
        rarity     = opp.get("rarity_signals") or []
        flags      = opp.get("red_flags") or []
        release_id = str(opp.get("release_id", "") or "")
        buy_url    = opp.get("listing_url", "") or ""
        page_url   = f"https://www.discogs.com/release/{release_id}" if release_id else ""

        rarity_str = "\n".join(f"  ✨ {s}" for s in rarity[:5]) if rarity else "  —"
        flags_str  = "\n".join(f"  ⚠️ {f}" for f in flags[:3])  if flags  else "  —"

        lp  = float(opp.get("listing_price", 0) or 0)
        med = float(opp.get("median_price", 0) or 0)
        est = float(opp.get("est_sell_price", 0) or 0)
        net = float(opp.get("gross_profit", 0) or 0)
        want = int(opp.get("wantlist_count", 0) or 0)
        sale = int(opp.get("num_for_sale", 0) or 0)

        msg = (
            f"🎵 <b>VINYL ARBITRAGE ALERT</b>\n\n"
            f"🎯 <b>Score {score:.1f}/10</b>  {_bar(score)}\n\n"
            f"<b>💿 {opp.get('artist','?')} — {opp.get('title','?')}</b>\n"
            f"🏷  {opp.get('label','?')} · {opp.get('year','?')} · {opp.get('country','?')}\n"
            f"📀 Condizione: {opp.get('condition','?')}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💸 <b>ECONOMIA</b>\n"
            f"• Prezzo più basso: <b>€{lp:.2f}</b>\n"
            f"• Mediana Discogs:  €{med:.2f}\n"
            f"• Vendi stimato:    €{est:.2f}\n"
            f"• Profitto netto:   <b>€{net:.2f}</b>\n"
            f"• ROI:             {_roi_emoji(roi)} <b>{roi*100:.0f}%</b>\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 <b>MERCATO</b>\n"
            f"• Want: {want:,}  |  In vendita: {sale}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✨ <b>RARITÀ</b>\n{rarity_str}\n\n"
            f"⛔ <b>RED FLAGS</b>\n{flags_str}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🛒 <b>COMPRA ORA</b>\n"
        )
        if buy_url:
            msg += f"👉 <a href=\"{buy_url}\">Marketplace (prezzo ↑)</a>\n"
        if page_url:
            msg += f"📖 <a href=\"{page_url}\">Scheda su Discogs</a>\n"
        msg += "━━━━━━━━━━━━━━━━"

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
        mode = "OAuth 🔐" if dc.HAS_OAUTH else "Token semplice ⚠️"
    except Exception:
        mode = "?"
    return _send(f"🚀 <b>Vinyl Scanner avviato</b>\nModalità: {mode}")
