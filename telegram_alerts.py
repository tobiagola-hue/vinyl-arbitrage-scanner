import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _send(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  Telegram non configurato"); return False
    url = f"https://api.telegram.org/bot{str(TELEGRAM_BOT_TOKEN).strip()}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": str(TELEGRAM_CHAT_ID).strip(),
            "text": text[:4096], "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)
        if r.status_code == 200: return True
        print(f"  Telegram {r.status_code}: {r.json().get('description','')}")
        return False
    except Exception as e:
        print(f"  Telegram exc: {e}"); return False


def _bar(score):
    try:
        f = max(0, min(10, round(float(score))))
        return "🟩"*f + "⬜"*(10-f)
    except Exception: return "⬜"*10


def _roi_e(roi):
    if roi >= 1.00: return "🚀"
    if roi >= 0.75: return "🔥"
    if roi >= 0.50: return "💰"
    return "✅"


def send_daily_recap(expensive_opps, midvalue_opps):
    """
    Alert unico alle 4:30 con:
    - Top 3 vinili costosi (Discogs->Discogs)
    - Top 10 vinili medio valore (eBay->Discogs)
    """
    from ebay_client import build_search_urls

    msg = "🌙 <b>VINYL ARBITRAGE — RECAP NOTTURNO 4:30</b>\n"
    msg += f"Analisi completa mezzanotte → 4:30\n\n"

    # TOP 3 EXPENSIVE
    msg += "━━━━━━━━━━━━━━━━\n"
    msg += "💎 <b>TOP 3 — ALTO VALORE (Discogs→Discogs)</b>\n"
    msg += "━━━━━━━━━━━━━━━━\n\n"

    if not expensive_opps:
        msg += "Nessuna opportunita trovata stanotte.\n\n"
    else:
        for i, opp in enumerate(expensive_opps[:3], 1):
            roi  = float(opp.get("roi",0) or 0)
            net  = float(opp.get("gross_profit",0) or 0)
            lp   = float(opp.get("listing_price",0) or 0)
            med  = float(opp.get("median_price",0) or 0)
            buy  = opp.get("listing_url","") or ""
            rel  = opp.get("release_url","") or ""
            sc   = float(opp.get("score",0) or 0)
            em   = "🥇" if i==1 else "🥈" if i==2 else "🥉"

            msg += f"{em} <b>{opp.get('artist','?')} — {opp.get('title','?')}</b>\n"
            msg += f"   {_bar(sc)} {sc:.1f}/10\n"
            msg += f"   Compra €{lp:.0f} → Vendi €{med:.0f} | ROI {_roi_e(roi)} {roi*100:.0f}% | +€{net:.0f}\n"
            if buy: msg += f"   🛒 <a href=\"{buy}\">Acquista su Discogs</a>\n"
            if rel: msg += f"   📖 <a href=\"{rel}\">Scheda Discogs</a>\n"
            msg += "\n"

    # TOP 10 MIDVALUE
    msg += "━━━━━━━━━━━━━━━━\n"
    msg += "🎯 <b>TOP 10 — MEDIO VALORE (eBay→Discogs)</b>\n"
    msg += "━━━━━━━━━━━━━━━━\n\n"

    if not midvalue_opps:
        msg += "Nessuna opportunita trovata oggi.\n"
    else:
        for i, opp in enumerate(midvalue_opps[:10], 1):
            roi     = float(opp.get("roi",0) or 0)
            net     = float(opp.get("gross_profit",0) or 0)
            lp      = float(opp.get("listing_price",0) or 0)
            buy     = opp.get("listing_url","") or ""
            rel     = opp.get("release_url","") or ""
            site    = opp.get("buy_site","eBay") or "eBay"
            notes   = opp.get("notes","") or ""
            artist  = opp.get("artist","?") or "?"
            title   = opp.get("title","?") or "?"

            msg += f"{i}. <b>{artist} — {title}</b>\n"
            msg += f"   €{lp:.0f} ({site}) → ROI {_roi_e(roi)} {roi*100:.0f}% | +€{net:.0f}\n"

            # Se il listing e incerto (versione non verificabile) -> solo Discogs
            if "incerto" in notes.lower():
                msg += f"   ⚠️ Versione non verificata — controlla manualmente\n"
                if rel: msg += f"   📖 <a href=\"{rel}\">Scheda Discogs</a>\n"
                urls = build_search_urls(artist, title)
                msg += f"   🔍 <a href=\"{urls['ebay_it']}\">Cerca su eBay IT</a> · <a href=\"{urls['ebay_uk']}\">eBay UK</a>\n"
            else:
                if buy: msg += f"   🛒 <a href=\"{buy}\">Acquista su {site}</a>\n"
                if rel: msg += f"   📖 <a href=\"{rel}\">Scheda Discogs</a>\n"

            msg += "\n"
            if len(msg) > 3800:
                msg += f"...e altri {len(midvalue_opps)-i} risultati\n"
                break

    return _send(msg)


def send_daily_summary(stats):
    try:
        msg = (f"📊 <b>Vinyl Scanner — Riassunto run</b>\n\n"
               f"🔍 Analizzati: {stats.get('scanned',0):,}\n"
               f"⚡ Trovati:    {stats.get('today_found',0)}\n"
               f"💰 Profitto storico: €{float(stats.get('total_profit_eur',0)):.2f}")
        return _send(msg)
    except Exception as e:
        print(f"  Err summary: {e}"); return False


def send_error_alert(error_msg):
    try: return _send(f"❌ <b>SCANNER ERROR</b>\n<code>{str(error_msg)[:400]}</code>")
    except Exception: return False


def send_startup_message(mode):
    try:
        import discogs_client as dc, ebay_client as ec
        auth = "OAuth" if dc.HAS_OAUTH else "Token"
        ebay = "ON" if ec.is_configured() else "OFF"
        label = "💎 Alto Valore" if mode=="expensive" else "🎯 Medio Valore"
        return _send(f"🚀 <b>Vinyl Scanner v15</b>\n{label} | {auth} | eBay {ebay}")
    except Exception:
        return _send("🚀 <b>Vinyl Scanner avviato</b>")
