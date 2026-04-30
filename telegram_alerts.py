"""
VINYL ARBITRAGE SCANNER — Telegram Alerts
Manda notifiche strutturate quando trova un'opportunità.
"""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _send(text: str, parse_mode: str = "HTML") -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️  Telegram non configurato (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID mancanti)")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"  Errore Telegram: {e}")
        return False


def _score_bar(score: float) -> str:
    """Converte score in barra visiva emoji."""
    filled = round(score)
    bar = "🟩" * filled + "⬜" * (10 - filled)
    return bar


def _roi_emoji(roi: float) -> str:
    if roi >= 1.00: return "🚀"
    if roi >= 0.75: return "🔥"
    if roi >= 0.60: return "💰"
    if roi >= 0.40: return "✅"
    return "⚠️"


def send_opportunity_alert(opp: dict):
    """Manda l'alert completo per un'opportunità trovata."""
    score       = opp.get("score", 0)
    roi         = opp.get("roi", 0)
    roi_emoji   = _roi_emoji(roi)
    score_bar   = _score_bar(score)
    rarity      = opp.get("rarity_signals", [])
    red_flags   = opp.get("red_flags", [])

    rarity_str   = "\n".join(f"  ✨ {s}" for s in rarity) if rarity else "  Nessuno"
    redflags_str = "\n".join(f"  ⚠️ {f}" for f in red_flags) if red_flags else "  Nessuno"

    msg = f"""
🎵 <b>VINYL ARBITRAGE ALERT</b>

🎯 <b>Score: {score}/10</b>
{score_bar}

<b>💿 {opp.get('artist', '?')} — {opp.get('title', '?')}</b>
🏷️  {opp.get('label', '?')} · {opp.get('year', '?')} · {opp.get('country', '?')}
📀  Condizione: <b>{opp.get('condition', '?')}</b>

━━━━━━━━━━━━━━━━━━━━
💸 <b>ANALISI ECONOMICA</b>
━━━━━━━━━━━━━━━━━━━━
• Prezzo listing:    <b>€{opp.get('listing_price', 0):.2f}</b>
• Mediana Discogs:   €{opp.get('median_price', 0):.2f}
• Vendi stimato a:   €{opp.get('est_sell_price', 0):.2f}
• Profitto netto:    <b>€{opp.get('gross_profit', 0):.2f}</b>
• ROI:              {roi_emoji} <b>{roi*100:.0f}%</b>
  (incl. spedizioni + fee Discogs)

━━━━━━━━━━━━━━━━━━━━
📊 <b>MERCATO</b>
━━━━━━━━━━━━━━━━━━━━
• Want: {opp.get('wantlist_count', 0):,}   |   In vendita: {opp.get('num_for_sale', 0)}
• Venditori: {opp.get('seller_username', '?')} ({opp.get('seller_rating', 0):.1f}% · {opp.get('seller_reviews', 0)} feedback)

━━━━━━━━━━━━━━━━━━━━
✨ <b>SEGNALI RARITÀ</b>
━━━━━━━━━━━━━━━━━━━━
{rarity_str}

⛔ <b>RED FLAGS</b>
{redflags_str}

━━━━━━━━━━━━━━━━━━━━
🔗 <a href="{opp.get('listing_url', '#')}">👉 APRI LISTING SU DISCOGS</a>
━━━━━━━━━━━━━━━━━━━━
""".strip()

    return _send(msg)


def send_daily_summary(stats: dict):
    """Manda riassunto giornaliero."""
    msg = f"""
📊 <b>VINYL ARBITRAGE — Riassunto Giornaliero</b>

🔍 Listing analizzati oggi: {stats.get('scanned', 0):,}
⚡ Opportunità trovate:      {stats.get('today_found', 0)}
📱 Alert inviati:           {stats.get('today_alerted', 0)}

━━━━━━━━━━━━━━━
📈 <b>Totale Storico</b>
• Alert totali inviati: {stats.get('total_alerted', 0)}
• Dischi acquistati:    {stats.get('total_purchases', 0)}
• Profitto netto:       €{stats.get('total_profit_eur', 0):.2f}
━━━━━━━━━━━━━━━
""".strip()
    return _send(msg)


def send_error_alert(error_msg: str):
    """Manda alert se lo scanner crasha."""
    return _send(f"❌ <b>VINYL SCANNER ERROR</b>\n\n<code>{error_msg}</code>")


def send_startup_message():
    return _send("🚀 <b>Vinyl Arbitrage Scanner avviato.</b>\nSto scansionando il marketplace Discogs...")
