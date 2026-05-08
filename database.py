"""
VINYL ARBITRAGE SCANNER — Database v2
Aggiunto supporto per mode (expensive/midvalue) e recap giornaliero.
"""
import sqlite3
import json
from datetime import datetime, date
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id       TEXT    UNIQUE,
            source           TEXT    DEFAULT 'discogs',
            mode             TEXT    DEFAULT 'expensive',
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
            alerted          INTEGER DEFAULT 0,
            created_at       TEXT,
            notes            TEXT
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
            notes             TEXT,
            FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id    INTEGER,
            sale_price     REAL,
            sale_date      TEXT,
            platform_sold  TEXT,
            fees_paid      REAL,
            shipping_paid  REAL,
            net_profit     REAL,
            notes          TEXT,
            FOREIGN KEY(purchase_id) REFERENCES purchases(id)
        )
    """)
    conn.commit()
    conn.close()


def opportunity_exists(listing_id: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM opportunities WHERE listing_id = ?", (listing_id,)
    ).fetchone()
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
                rarity_signals, red_flags,
                wantlist_count, num_for_sale,
                seller_username, seller_rating, seller_reviews,
                listing_url, release_url, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            opp["listing_id"],
            opp.get("source", "discogs"),
            opp.get("mode", "expensive"),
            opp.get("release_id", ""),
            opp.get("artist", ""),
            opp.get("title", ""),
            opp.get("label", ""),
            opp.get("year", ""),
            opp.get("country", ""),
            opp.get("condition", ""),
            opp.get("listing_price", 0),
            opp.get("median_price", 0),
            opp.get("est_sell_price", 0),
            opp.get("gross_profit", 0),
            opp.get("roi", 0),
            opp.get("score", 0),
            json.dumps(opp.get("rarity_signals", [])),
            json.dumps(opp.get("red_flags", [])),
            opp.get("wantlist_count", 0),
            opp.get("num_for_sale", 0),
            opp.get("seller_username", ""),
            opp.get("seller_rating", 0),
            opp.get("seller_reviews", 0),
            opp.get("listing_url", ""),
            opp.get("release_url", ""),
            datetime.now().isoformat(),
        ))
        conn.commit()
    finally:
        conn.close()


def mark_alerted(listing_id: str):
    conn = get_conn()
    conn.execute(
        "UPDATE opportunities SET alerted = 1 WHERE listing_id = ?", (listing_id,)
    )
    conn.commit()
    conn.close()


def get_today_stats() -> dict:
    today = date.today().isoformat()
    conn = get_conn()
    found = conn.execute(
        "SELECT COUNT(*) FROM opportunities WHERE created_at LIKE ?", (f"{today}%",)
    ).fetchone()[0]
    alerted = conn.execute(
        "SELECT COUNT(*) FROM opportunities WHERE alerted=1 AND created_at LIKE ?",
        (f"{today}%",)
    ).fetchone()[0]
    conn.close()
    return {"today_found": found, "today_alerted": alerted}


def get_all_time_stats() -> dict:
    conn = get_conn()
    total_alerted = conn.execute(
        "SELECT COUNT(*) FROM opportunities WHERE alerted=1"
    ).fetchone()[0]
    total_purchases = conn.execute("SELECT COUNT(*) FROM purchases").fetchone()[0]
    total_profit = conn.execute(
        "SELECT COALESCE(SUM(net_profit), 0) FROM sales"
    ).fetchone()[0]
    conn.close()
    return {
        "total_alerted": total_alerted,
        "total_purchases": total_purchases,
        "total_profit_eur": round(total_profit, 2),
    }


def get_top_opportunities(mode: str, limit: int = 10, days: int = 1) -> list:
    """Ritorna le migliori opportunità delle ultime N ore per il recap."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT artist, title, listing_price, median_price, gross_profit,
               roi, score, listing_url, release_url, wantlist_count
        FROM opportunities
        WHERE mode = ?
          AND created_at >= datetime('now', ?)
        ORDER BY score DESC, roi DESC
        LIMIT ?
    """, (mode, f"-{days} days", limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_purchase(opportunity_id, purchase_price, condition_received,
                 platform, shipping_in, notes=""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO purchases
        (opportunity_id, purchase_price, purchase_date, condition_received,
         platform_bought, shipping_paid_in, notes)
        VALUES (?,?,?,?,?,?,?)
    """, (opportunity_id, purchase_price, datetime.now().isoformat(),
          condition_received, platform, shipping_in, notes))
    conn.commit()
    conn.close()


def log_sale(purchase_id, sale_price, platform, fees_paid, shipping_paid, notes=""):
    net = sale_price - fees_paid - shipping_paid
    conn = get_conn()
    conn.execute("""
        INSERT INTO sales
        (purchase_id, sale_price, sale_date, platform_sold,
         fees_paid, shipping_paid, net_profit, notes)
        VALUES (?,?,?,?,?,?,?,?)
    """, (purchase_id, sale_price, datetime.now().isoformat(),
          platform, fees_paid, shipping_paid, net, notes))
    conn.commit()
    conn.close()
    return net
