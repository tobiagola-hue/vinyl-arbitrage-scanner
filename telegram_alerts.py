import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _send(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  Telegram non configurato")
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
        desc = r.json().get("description","")
        if "chat not found" in desc:
            print("  Telegram: scrivi /start al bot")
        else:
            print(f"  Telegram {r.status_code}: {desc}")
        return False
    except Exception as e:
        print(f"  Telegram exception: {e}")
        return False


def _bar(score):
    try:
        f = max(0, min(10, round(float(score))))
        return "🟩"*f + "⬜"*(10-f)
    except Exception:
        return "⬜"*10


def _roi_e(roi):
    if roi >= 1.00: return "🚀"
    if roi >= 0.75: return "🔥"
    if roi >= 0.50: return "💰"
    return "✅"


def send_opportunity_alert(opp):
    try:
        score  = float(opp.get("score",0) or 0)
        roi    = float(opp.get("roi",0) or 0)
        lp     = float(opp.get("listing_price",0) or 0)
        med    = float(opp.get("median_price",0) or 0)
        est    = float(opp.get("est_sell_price",0) or 0)
        net    = float(opp.get("gross_profit",0) or 0)
        want   = int(opp.get("wantlist_count",0) or 0)
        sale   = int(opp.get("num_for_sale",0) or 0)
        artist = opp.get("artist","?") or "?"
        title  = opp.get("title","?") or "?"
        mode   = opp.get("mode","expensive")
        rid    = str(opp.get("release_id","") or "")
        site   = opp.get("buy_site","Discogs")

        rarity = opp.get("rarity_signals") or []
        flags  = opp.get("red_flags") or []
        rarity_str = "\n".join(f"  ✨ {s}" for s in rarity[:4]) if rarity else "  —"
        flags_str  = "\n".join(f"  ⚠️ {f}" for f in flags[:3])  if flags  else "  —"

        buy_url     = opp.get("listing_url","") or ""
        release_url = opp.get("release_url","") or f"https://www.discogs.com/release/{rid}"

        mode_label = "💎 ALTO VALORE" if mode=="expensive" else "🎯 MEDIO VALORE"
        site_emoji = "🟡" if "ebay" in site.lower() else "💚"

        # Guida condizioni per acquisti da siti resale
        if mode == "midvalue":
            cond_guide = (
                "\n\n📋 <b>GUIDA CONDIZIONI → DISCOGS</b>\n"
                "• Come nuovo / Perfetto → NM (€{:.0f})\n"
                "• Ottime condizioni     → VG+ (€{:.0f})\n"
                "• Buone condizioni      → VG  (€{:.0f})\n"
                "• Usato                 → G+  (€{:.0f})"
            ).format(med*1.0, med*0.90, med*0.70, med*0.40)
        else:
            cond_guide = ""

        # Link acquisto + altri marketplace
        from ebay_client import build_search_urls
        links = build_search_urls(artist, title)

        msg = (
            f"🎵 <b>VINYL ARBITRAGE — {mode_label}</b>\n\n"
            f"🎯 <b>Score {score:.1f}/10</b>  {_bar(score)}\n\n"
            f"<b>💿 {artist} — {title}</b>\n"
            f"🏷  {opp.get('label','?')} · {opp.get('year','?')} · {opp.get('country','?')}\n"
            f"📀 Condizione: {opp.get('condition','?')}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💸 <b>ECONOMIA</b>\n"
            f"• Prezzo acquisto:  <b>€{lp:.2f}</b> ({site})\n"
            f"• Mediana Discogs:  €{med:.2f}\n"
            f"• Rivendi su Discogs: €{est:.2f}\n"
            f"• Profitto netto:   <b>€{net:.2f}</b>\n"
            f"• ROI:             {_roi_e(roi)} <b>{roi*100:.0f}%</b>\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📊 <b>MERCATO DISCOGS</b>\n"
            f"• Wantlist: {want:,}  |  In vendita: {sale}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"✨ <b>RARITÀ</b>\n{rarity_str}\n\n"
            f"⛔ <b>RED FLAGS</b>\n{flags_str}"
            f"{cond_guide}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🛒 <b>COMPRA QUI</b>\n"
        )

        if buy_url:
            msg += f"{site_emoji} <a href=\"{buy_url}\">Acquista su {site} (prezzo migliore trovato)</a>\n"

        # Link di ricerca sugli altri siti
        msg += f"🟡 <a href=\"{links['ebay_it']}\">Cerca su eBay Italia</a>\n"
        msg += f"🟡 <a href=\"{links['ebay_uk']}\">Cerca su eBay UK</a>\n"
        msg += f"🔵 <a href=\"{links['vinted']}\">Cerca su Vinted</a>\n"
        msg += f"🟠 <a href=\"{links['wallapop']}\">Cerca su Wallapop</a>\n"
        msg += f"🔴 <a href=\"{links['subito']}\">Cerca su Subito.it</a>\n"
        msg += f"\n📖 <a href=\"{release_url}\">Scheda disco su Discogs</a>\n"
        msg += "━━━━━━━━━━━━━━━━"

        return _send(msg)
    except Exception as e:
        print(f"  Errore alert: {e}")
        return False


def send_recap_expensive(opportunities):
    if not opportunities:
        return _send("📊 <b>Recap 7:00 — Alto Valore</b>\n\nNessuna opportunità nelle ultime 24h.")
    msg = "☀️ <b>RECAP 7:00 — TOP 3 ALTO VALORE</b>\nMigliori 24h su Discogs\n\n"
    for i, opp in enumerate(opportunities[:3], 1):
        roi = float(opp.get("roi",0) or 0)
        net = float(opp.get("gross_profit",0) or 0)
        lp  = float(opp.get("listing_price",0) or 0)
        buy = opp.get("listing_url","") or ""
        rel = opp.get("release_url","") or ""
        e   = "🥇" if i==1 else "🥈" if i==2 else "🥉"
        msg += f"{e} <b>{opp.get('artist','?')} — {opp.get('title','?')}</b>\n"
        msg += f"   €{lp:.0f} → ROI {roi*100:.0f}% → +€{net:.0f}\n"
        if buy: msg += f"   🛒 <a href=\"{buy}\">Compra</a>"
        if rel: msg += f" · 📖 <a href=\"{rel}\">Discogs</a>"
        msg += "\n\n"
    return _send(msg)


def send_recap_midvalue(opportunities, slot="13:00"):
    if not opportunities:
        return _send(f"📊 <b>Recap {slot} — Medio Valore</b>\n\nNessuna opportunità nelle ultime 24h.")
    e = "🌞" if slot=="13:00" else "🌆"
    msg = f"{e} <b>RECAP {slot} — TOP 10 MEDIO VALORE</b>\nOrdinati per vantaggio\n\n"
    for i, opp in enumerate(opportunities[:10], 1):
        roi  = float(opp.get("roi",0) or 0)
        net  = float(opp.get("gross_profit",0) or 0)
        lp   = float(opp.get("listing_price",0) or 0)
        buy  = opp.get("listing_url","") or ""
        rel  = opp.get("release_url","") or ""
        site = opp.get("buy_site","") or "Discogs"
        msg += f"{i}. <b>{opp.get('artist','?')} — {opp.get('title','?')}</b>\n"
        msg += f"   €{lp:.0f} ({site}) → ROI {roi*100:.0f}% → +€{net:.0f}\n"
        if buy: msg += f"   🛒 <a href=\"{buy}\">Compra</a>"
        if rel: msg += f" · 📖 <a href=\"{rel}\">Discogs</a>"
        msg += "\n\n"
        if len(msg) > 3500:
            break
    return _send(msg)


def send_daily_summary(stats):
    try:
        msg = (
            f"📊 <b>Vinyl Scanner — Riassunto run</b>\n\n"
            f"🔍 Analizzati: {stats.get('scanned',0):,}\n"
            f"⚡ Trovati:    {stats.get('today_found',0)}\n"
            f"📱 Alert:      {stats.get('today_alerted',0)}\n\n"
            f"💰 Profitto storico: €{float(stats.get('total_profit_eur',0)):.2f}"
        )
        return _send(msg)
    except Exception as e:
        print(f"  Errore summary: {e}")
        return False


def send_error_alert(error_msg):
    try: return _send(f"❌ <b>SCANNER ERROR</b>\n<code>{str(error_msg)[:400]}</code>")
    except Exception: return False


def send_startup_message(mode):
    try:
        import discogs_client as dc
        import ebay_client as ec
        auth = "OAuth" if dc.HAS_OAUTH else "Token"
        ebay = "eBay ON" if ec.is_configured() else "eBay OFF"
        label = "💎 Alto Valore" if mode=="expensive" else "🎯 Medio Valore"
        return _send(f"🚀 <b>Vinyl Scanner avviato</b>\n{label} | {auth} | {ebay}")
    except Exception:
        return _send(f"🚀 <b>Vinyl Scanner avviato</b>")
