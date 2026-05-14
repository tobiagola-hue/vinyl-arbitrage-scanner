import sqlite3, json
from datetime import datetime, date
from config import DB_PATH


def get_conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    conn = get_conn()
    c = conn.cursor()
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
            created_at       TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id    INTEGER,
            purchase_price    REAL,
            purchase_date     TEXT,
            condition_received TEXT,
            platform_bought   TEXT,
            shipping_paid_in  REAL,
            notes             TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id   INTEGER,
            sale_price    REAL,
            sale_date     TEXT,
            platform_sold TEXT,
            fees_paid     REAL,
            shipping_paid REAL,
            net_profit    REAL,
            notes         TEXT
        )
    """)
    conn.commit()

    # Migrazione automatica colonne mancanti
    migrations = [
        "ALTER TABLE opportunities ADD COLUMN release_url TEXT",
        "ALTER TABLE opportunities ADD COLUMN mode TEXT DEFAULT 'expensive'",
        "ALTER TABLE opportunities ADD COLUMN buy_site TEXT",
    ]
    for sql in migrations:
        try: c.execute(sql)
        except Exception: pass
    conn.commit()
    conn.close()


def opportunity_exists(listing_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM opportunities WHERE listing_id=?", (listing_id,)
    ).fetchone()
    conn.close()
    return row is not None


def save_opportunity(opp):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO opportunities (
                listing_id, source, mode, release_id, artist, title, label,
                year, country, condition, listing_price, median_price,
                est_sell_price, gross_profit, roi, score,
                rarity_signals, red_flags, wantlist_count, num_for_sale,
                seller_username, seller_rating, seller_reviews,
                listing_url, release_url, buy_site, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            opp["listing_id"], opp.get("source","discogs"),
            opp.get("mode","expensive"), opp.get("release_id",""),
            opp.get("artist",""), opp.get("title",""),
            opp.get("label",""), opp.get("year",""), opp.get("country",""),
            opp.get("condition",""), opp.get("listing_price",0),
            opp.get("median_price",0), opp.get("est_sell_price",0),
            opp.get("gross_profit",0), opp.get("roi",0), opp.get("score",0),
            json.dumps(opp.get("rarity_signals",[])),
            json.dumps(opp.get("red_flags",[])),
            opp.get("wantlist_count",0), opp.get("num_for_sale",0),
            opp.get("seller_username",""), opp.get("seller_rating",0),
            opp.get("seller_reviews",0), opp.get("listing_url",""),
            opp.get("release_url",""), opp.get("buy_site","discogs"),
            datetime.now().isoformat(),
        ))
        conn.commit()
    finally:
        conn.close()


def mark_alerted(listing_id):
    conn = get_conn()
    conn.execute("UPDATE opportunities SET alerted=1 WHERE listing_id=?", (listing_id,))
    conn.commit()
    conn.close()


def get_today_stats():
    today = date.today().isoformat()
    conn = get_conn()
    found   = conn.execute("SELECT COUNT(*) FROM opportunities WHERE created_at LIKE ?", (f"{today}%",)).fetchone()[0]
    alerted = conn.execute("SELECT COUNT(*) FROM opportunities WHERE alerted=1 AND created_at LIKE ?", (f"{today}%",)).fetchone()[0]
    conn.close()
    return {"today_found": found, "today_alerted": alerted}


def get_all_time_stats():
    conn = get_conn()
    alerted   = conn.execute("SELECT COUNT(*) FROM opportunities WHERE alerted=1").fetchone()[0]
    purchases = conn.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
    profit    = conn.execute("SELECT COALESCE(SUM(net_profit),0) FROM sales").fetchone()[0]
    conn.close()
    return {"total_alerted": alerted, "total_purchases": purchases, "total_profit_eur": round(profit,2)}


def get_top_opportunities(mode, limit=10, days=1):
    conn = get_conn()
    rows = conn.execute("""
        SELECT artist, title, listing_price, median_price, gross_profit,
               roi, score, listing_url, release_url, wantlist_count, buy_site
        FROM opportunities
        WHERE mode=? AND created_at >= datetime('now', ?)
        ORDER BY score DESC, roi DESC LIMIT ?
    """, (mode, f"-{days} days", limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
