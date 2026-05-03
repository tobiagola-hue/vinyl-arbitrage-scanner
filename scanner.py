"""
VINYL ARBITRAGE SCANNER — scanner.py v7
Robusto contro tutti gli errori. 
Con OAuth: price_suggestions reali + listing individuali.
Senza OAuth: lowest_price * 1.8 come stima mediana (fallback automatico).
Alert Telegram include sempre link acquisto diretto.
"""
import time
import traceback

import discogs_client as dc
from database import (
    init_db, opportunity_exists, save_opportunity,
    mark_alerted, get_today_stats, get_all_time_stats
)
from scorer import (
    calc_profit, score_opportunity, find_rarity_signals,
    find_red_flags, detect_first_press_from_matrix, detect_engineer_initials
)
from telegram_alerts import (
    send_opportunity_alert, send_daily_summary,
    send_error_alert, send_startup_message
)
from watchlist import WATCHLIST
from config import (
    MIN_SCORE, MIN_MEDIAN_EUR, MAX_PRICE_RATIO,
    MIN_PROFIT_EUR, MIN_ROI
)

MAX_RESULTS_PER_QUERY = 8
MIN_WANTLIST          = 20
FALLBACK_MEDIAN_MULT  = 1.8   # Stima mediana senza OAuth: lowest * 1.8


def safe_get(d, *keys, default=None):
    """Naviga dict annidati senza crash."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def get_artist_name(details: dict) -> str:
    """Estrae nome artista principale in modo sicuro."""
    try:
        artists = details.get("artists") or []
        if artists and isinstance(artists, list):
            name = artists[0].get("name", "")
            if name:
                return name
        # Fallback: prendi dalla stringa titolo
        title = details.get("title", "?")
        return title.split(" - ")[0].strip() if " - " in title else "?"
    except Exception:
        return "?"


def get_label_name(details: dict) -> str:
    """Estrae nome label in modo sicuro."""
    try:
        labels = details.get("labels") or []
        if labels and isinstance(labels, list):
            return labels[0].get("name", "")
        return ""
    except Exception:
        return ""


def get_median(release_id: int, lowest: float) -> tuple:
    """
    Ritorna (mediana, condizione_riferimento).
    Strategia 1 (OAuth): usa price_suggestions ufficiali Discogs.
    Strategia 2 (fallback): stima lowest_price * FALLBACK_MEDIAN_MULT.
    """
    # Prova con OAuth prima
    suggestions = dc.get_price_suggestions(release_id)
    if suggestions and isinstance(suggestions, dict):
        for cond in ("Near Mint (NM or M-)", "Very Good Plus (VG+)", "Mint (M)", "Very Good (VG)"):
            try:
                val = safe_get(suggestions, cond, "value")
                if val and float(val) > 0:
                    return float(val), cond
            except (ValueError, TypeError):
                continue

    # Fallback: stima da lowest_price
    if lowest and float(lowest) > 0:
        return round(float(lowest) * FALLBACK_MEDIAN_MULT, 2), "Very Good Plus (VG+)"

    return 0.0, ""


def extract_listing_price(listing: dict) -> float:
    """Estrae prezzo da un listing (può essere dict o numero)."""
    try:
        p = listing.get("price") or 0
        if isinstance(p, dict):
            return float(p.get("value", 0) or 0)
        return float(p or 0)
    except (ValueError, TypeError):
        return 0.0


def analyze_release(release_id: int) -> int:
    """
    Analizza una release. Ritorna 1 se trova e alerta un'opportunità.
    Gestisce ogni possibile eccezione internamente.
    """
    try:
        details = dc.get_release_details(release_id)
        if not details or not isinstance(details, dict):
            return 0

        # ── Estrai dati base ──────────────────────────────
        artist   = get_artist_name(details)
        title    = details.get("title", "?") or "?"
        label    = get_label_name(details)
        year     = str(details.get("year", "") or "")
        country  = details.get("country", "US") or "US"
        notes    = details.get("notes", "") or ""

        try:
            wantlist = int(safe_get(details, "community", "want", default=0) or 0)
        except (ValueError, TypeError):
            wantlist = 0

        try:
            for_sale = int(details.get("num_for_sale", 0) or 0)
        except (ValueError, TypeError):
            for_sale = 0

        try:
            lowest = float(details.get("lowest_price", 0) or 0)
        except (ValueError, TypeError):
            lowest = 0.0

        # ── Filtri rapidi ─────────────────────────────────
        if wantlist < MIN_WANTLIST:
            print(f"      ↳ Skip: want={wantlist} < {MIN_WANTLIST}")
            return 0

        if for_sale < 1:
            print(f"      ↳ Skip: nessuno in vendita")
            return 0

        if lowest <= 0:
            print(f"      ↳ Skip: lowest_price non disponibile")
            return 0

        # ── Calcola mediana ───────────────────────────────
        median, ref_cond = get_median(release_id, lowest)

        if median <= 0:
            print(f"      ↳ Skip: mediana non calcolabile")
            return 0

        if median < MIN_MEDIAN_EUR:
            print(f"      ↳ Skip: mediana €{median:.0f} < soglia €{MIN_MEDIAN_EUR}")
            return 0

        ratio  = lowest / median if median > 0 else 1.0
        source = "OAuth" if dc.HAS_OAUTH else "stima"
        print(
            f"      ↳ want={wantlist} | "
            f"lowest=€{lowest:.0f} | mediana=€{median:.0f} ({source}) | "
            f"ratio={ratio:.0%} | in vendita={for_sale}"
        )

        if ratio > MAX_PRICE_RATIO:
            print(f"      ↳ Skip: ratio {ratio:.0%} > {MAX_PRICE_RATIO:.0%}")
            return 0

        # ── Già analizzata? ───────────────────────────────
        opp_id = f"release_{release_id}"
        if opportunity_exists(opp_id):
            print(f"      ↳ Già nel database")
            return 0

        # ── Dati acquisto (listing reale se OAuth disponibile) ──
        buy_price = lowest
        condition = ref_cond
        seller_name    = "vedi link"
        seller_rating  = 100.0
        seller_reviews = 0

        if dc.HAS_OAUTH:
            try:
                listings = dc.get_marketplace_listings(release_id)
                if listings and isinstance(listings, list) and len(listings) > 0:
                    first     = listings[0]
                    lp        = extract_listing_price(first)
                    if lp > 0:
                        buy_price = lp
                    cond = first.get("condition", "") or ""
                    if cond:
                        condition = cond
                    s = first.get("seller") or {}
                    seller_name    = s.get("username", "vedi link") or "vedi link"
                    seller_rating  = float(safe_get(s, "stats", "rating") or 100)
                    seller_reviews = int(safe_get(s, "stats", "total") or 0)
            except Exception:
                pass  # Fallback ai valori default già impostati

        # ── Analisi testo ─────────────────────────────────
        full_text   = f"{artist} {title} {label} {notes}".lower()
        rarity_sigs = find_rarity_signals(full_text)
        flags       = find_red_flags(full_text)

        try:
            if detect_first_press_from_matrix(notes):
                rarity_sigs.append("first press (matrix detected)")
        except Exception:
            pass

        try:
            for eng in detect_engineer_initials(notes):
                rarity_sigs.append(f"engineer: {eng}")
        except Exception:
            pass

        # ── Calcolo profitto ──────────────────────────────
        try:
            profit_data = calc_profit(buy_price, median, condition, country)
        except Exception:
            return 0

        if profit_data.get("gross_profit", 0) < MIN_PROFIT_EUR:
            print(f"      ↳ Skip: profitto €{profit_data.get('gross_profit',0):.0f} < €{MIN_PROFIT_EUR}")
            return 0

        if profit_data.get("roi", 0) < MIN_ROI:
            print(f"      ↳ Skip: ROI {profit_data.get('roi',0)*100:.0f}% < {MIN_ROI*100:.0f}%")
            return 0

        # ── Costruisce e salva opportunità ────────────────
        opp = {
            "listing_id":      opp_id,
            "source":          "discogs",
            "release_id":      str(release_id),
            "artist":          artist,
            "title":           title,
            "label":           label,
            "year":            year,
            "country":         country,
            "condition":       condition,
            "listing_price":   buy_price,
            "median_price":    median,
            "est_sell_price":  profit_data.get("est_sell_price", 0),
            "gross_profit":    profit_data.get("gross_profit", 0),
            "roi":             profit_data.get("roi", 0),
            "rarity_signals":  rarity_sigs,
            "red_flags":       flags,
            "wantlist_count":  wantlist,
            "num_for_sale":    for_sale,
            "seller_username": seller_name,
            "seller_rating":   seller_rating,
            "seller_reviews":  seller_reviews,
            "listing_url":     dc.get_marketplace_url(release_id),
        }

        try:
            opp["score"] = score_opportunity(opp)
        except Exception:
            opp["score"] = 5.0

        try:
            save_opportunity(opp)
        except Exception:
            pass

        print(
            f"    💎 {artist} — {title} | "
            f"€{buy_price:.0f} vs €{median:.0f} | "
            f"ROI {opp['roi']*100:.0f}% | Score {opp['score']}/10"
        )

        # ── Alert Telegram ────────────────────────────────
        if opp["score"] >= MIN_SCORE:
            try:
                if send_opportunity_alert(opp):
                    mark_alerted(opp_id)
                    print(f"    ✅ ALERT INVIATO — Score {opp['score']}/10")
                    time.sleep(2)
            except Exception as e:
                print(f"    ⚠️ Telegram error: {e}")
            return 1

        return 0

    except Exception as e:
        print(f"    ⚠️ Errore release {release_id}: {e}")
        return 0


def scan_query(query: str, name: str, tier: str) -> int:
    """Cerca e analizza release da una query. Gestisce tutti gli errori."""
    print(f"\n🔎 [{tier}] {name}")

    try:
        results = dc.search_releases(query=query)
    except Exception as e:
        print(f"    Errore search: {e}")
        return 0

    if not results or not isinstance(results, dict):
        print(f"    Nessun risultato")
        return 0

    releases = (results.get("results") or [])[:MAX_RESULTS_PER_QUERY]
    if not releases:
        print(f"    Lista risultati vuota")
        return 0

    found = 0
    for r in releases:
        try:
            rid = r.get("id")
            if not rid:
                continue
            t = r.get("title", "?") or "?"
            print(f"  → {t} [{rid}]")
            found += analyze_release(rid)
        except Exception as e:
            print(f"    ⚠️ Errore su risultato: {e}")
            continue
        time.sleep(0.8)

    return found


def main():
    mode = "OAuth 🔐 (piena)" if dc.HAS_OAUTH else "Token ⚠️ (fallback mediana stimata)"
    print("=" * 55)
    print(f"🎵 VINYL ARBITRAGE SCANNER v7")
    print(f"   Modalità: {mode}")
    print("=" * 55)

    try:
        init_db()
    except Exception as e:
        print(f"❌ Errore DB: {e}")
        return

    try:
        send_startup_message()
    except Exception:
        pass

    for tier in ("A", "B", "C"):
        entries = [e for e in WATCHLIST if e.get("tier") == tier]
        print(f"\n{'='*20} TIER {tier} — {len(entries)} ricerche {'='*20}")
        for entry in entries:
            try:
                scan_query(
                    query=entry.get("query", ""),
                    name=entry.get("name", "?"),
                    tier=tier
                )
            except Exception as e:
                print(f"  ❌ {entry.get('name', '?')}: {e}")
            time.sleep(1)

    try:
        today   = get_today_stats()
        alltime = get_all_time_stats()
        print(f"\n✅ Completato | Trovate: {today['today_found']} | Alert: {today['today_alerted']}")
        send_daily_summary({
            "scanned":       len(WATCHLIST) * MAX_RESULTS_PER_QUERY,
            "today_found":   today["today_found"],
            "today_alerted": today["today_alerted"],
            **alltime,
        })
    except Exception as e:
        print(f"❌ Errore sommario: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Interrotto manualmente")
    except Exception as e:
        msg = traceback.format_exc()
        print(f"\n❌ ERRORE CRITICO:\n{msg}")
        try:
            send_error_alert(str(e)[:500])
        except Exception:
            pass
