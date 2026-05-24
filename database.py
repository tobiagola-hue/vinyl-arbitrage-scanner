import sqlite3, json
from datetime import datetime, date, timedelta
from config import DB_PATH


def get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id       TEXT UNIQUE,
            source           TEXT DEFAULT 'discogs',
            mode             TEXT DEFAULT 'expensive',
            release_id       TEXT,
            artist           TEXT,
            title            TEXT,
            label            TEXT,
            year             TEXT,
            country          TEXT,
            condition        TEXT,
            listing_price    REAL,
            median_price     REAL,
            est_sell_price   REAL,
            gross_profit     REAL,
            roi              REAL,
            score            REAL,
            rarity_signals   TEXT,
            red_flags        TEXT,
            wantlist_count   INTEGER DEFAULT 0,
            num_for_sale     INTEGER DEFAULT 0,
            seller_username  TEXT,
            seller_rating    REAL,
            seller_reviews   INTEGER,
            listing_url      TEXT,
            release_url      TEXT,
            buy_site         TEXT,
            alerted          INTEGER DEFAULT 0,
            created_at       TEXT,
            notes            TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS seen_releases (
            release_id  TEXT PRIMARY KEY,
            mode        TEXT,
            seen_at     TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER, purchase_price REAL,
            purchase_date TEXT, condition_received TEXT,
            platform_bought TEXT, shipping_paid_in REAL, notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER, sale_price REAL, sale_date TEXT,
            platform_sold TEXT, fees_paid REAL, shipping_paid REAL,
            net_profit REAL, notes TEXT
        )
    """)
    conn.commit()
    # Migrazioni
    for sql in [
        "ALTER TABLE opportunities ADD COLUMN release_url TEXT",
        "ALTER TABLE opportunities ADD COLUMN mode TEXT DEFAULT 'expensive'",
        "ALTER TABLE opportunities ADD COLUMN buy_site TEXT",
        "ALTER TABLE opportunities ADD COLUMN notes TEXT",
    ]:
        try: c.execute(sql)
        except Exception: pass
    conn.commit()
    conn.close()


def was_seen_recently(release_id: str, mode: str, days: int = 7) -> bool:
    """Controlla se la release e stata analizzata negli ultimi N giorni."""
    conn = get_conn()
    row = conn.execute(
        "SELECT seen_at FROM seen_releases WHERE release_id=? AND mode=?",
        (str(release_id), mode)
    ).fetchone()
    conn.close()
    if not row: return False
    try:
        seen = datetime.fromisoformat(row["seen_at"]).date()
        return (date.today() - seen).days < days
    except Exception:
        return False


def mark_seen(release_id: str, mode: str):
    """Registra che la release e stata analizzata oggi."""
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO seen_releases (release_id, mode, seen_at) VALUES (?,?,?)",
        (str(release_id), mode, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def opportunity_exists(listing_id: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT id FROM opportunities WHERE listing_id=?", (listing_id,)).fetchone()
    conn.close()
    return row is not None


def save_opportunity(opp: dict):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO opportunities (
                listing_id, source, mode, release_id, artist, title, label,
                year, country, condition, listing_price, median_price,
                est_sell_price, gross_profit, roi, score,
                rarity_signals, red_flags, wantlist_count, num_for_sale,
                seller_username, seller_rating, seller_reviews,
                listing_url, release_url, buy_site, created_at, notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            opp["listing_id"], opp.get("source","discogs"), opp.get("mode","expensive"),
            opp.get("release_id",""), opp.get("artist",""), opp.get("title",""),
            opp.get("label",""), opp.get("year",""), opp.get("country",""),
            opp.get("condition",""), opp.get("listing_price",0), opp.get("median_price",0),
            opp.get("est_sell_price",0), opp.get("gross_profit",0), opp.get("roi",0),
            opp.get("score",0),
            json.dumps(opp.get("rarity_signals",[])), json.dumps(opp.get("red_flags",[])),
            opp.get("wantlist_count",0), opp.get("num_for_sale",0),
            opp.get("seller_username",""), opp.get("seller_rating",0),
            opp.get("seller_reviews",0), opp.get("listing_url",""),
            opp.get("release_url",""), opp.get("buy_site","Discogs"),
            datetime.now().isoformat(), opp.get("notes","")
        ))
        conn.commit()
    finally:
        conn.close()


def mark_alerted(listing_id: str):
    conn = get_conn()
    conn.execute("UPDATE opportunities SET alerted=1 WHERE listing_id=?", (listing_id,))
    conn.commit(); conn.close()


def get_today_stats():
    today = date.today().isoformat()
    conn = get_conn()
    found   = conn.execute("SELECT COUNT(*) FROM opportunities WHERE created_at LIKE ?", (f"{today}%",)).fetchone()[0]
    alerted = conn.execute("SELECT COUNT(*) FROM opportunities WHERE alerted=1 AND created_at LIKE ?", (f"{today}%",)).fetchone()[0]
    conn.close()
    return {"today_found": found, "today_alerted": alerted}


def get_all_time_stats():
    conn = get_conn()
    a = conn.execute("SELECT COUNT(*) FROM opportunities WHERE alerted=1").fetchone()[0]
    p = conn.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
    pr= conn.execute("SELECT COALESCE(SUM(net_profit),0) FROM sales").fetchone()[0]
    conn.close()
    return {"total_alerted": a, "total_purchases": p, "total_profit_eur": round(pr,2)}


def get_top_opportunities(mode: str, limit: int = 10, hours: int = 24) -> list:
    """Migliori opportunita delle ultime N ore, per il recap."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT artist, title, listing_price, median_price, gross_profit,
               roi, score, listing_url, release_url, wantlist_count, buy_site, notes
        FROM opportunities
        WHERE mode=? AND created_at >= datetime('now', ?)
        ORDER BY score DESC, roi DESC LIMIT ?
    """, (mode, f"-{hours} hours", limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
