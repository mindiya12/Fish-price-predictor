"""
Fuel Price Scraper - Ceypetco Historical Prices
================================================
Scrapes historical fuel prices from ceypetco.gov.lk and stores them
in the `fuel_prices` table.

Table structure confirmed:
  Date (DD.MM.YYYY) | LP 95 | LP 92 | LAD | LSD | LK | LIK | FUR...

Model feature mapping:
  LP 95 -> LP 95
  LP 92 -> LP 92
  LAD   -> LAD
  LSD   -> LSD
  LK    -> LK
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = os.environ.get("DATABASE_URL")

CEYPETCO_URL = "https://ceypetco.gov.lk/historical-prices/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}


def _create_table(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fuel_prices (
            id         SERIAL PRIMARY KEY,
            date       DATE NOT NULL UNIQUE,
            lp_95      NUMERIC,
            lp_92      NUMERIC,
            lad        NUMERIC,
            lsd        NUMERIC,
            lk         NUMERIC,
            source     TEXT DEFAULT 'ceypetco',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """))


def _parse_date(val: str):
    """Parse DD.MM.YYYY or MM/DD/YYYY or YYYY-MM-DD."""
    val = val.strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def _parse_price(val: str):
    """Strip non-numeric characters and parse to float."""
    import re
    cleaned = re.sub(r"[^\d.]", "", val.strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def scrape_fuel_prices() -> pd.DataFrame:
    """
    Fetch and parse the Ceypetco historical prices page.
    Returns a DataFrame with columns: date, lp_95, lp_92, lad, lsd, lk
    """
    resp = requests.get(CEYPETCO_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # The price table is inside a div.table-container
    table = soup.find("table")
    if not table:
        raise RuntimeError("Could not find price table on Ceypetco page.")

    rows = table.find_all("tr")
    if not rows:
        raise RuntimeError("Price table has no rows.")

    # Parse header row to build column index map
    header_cells = [th.get_text(strip=True).upper() for th in rows[0].find_all(["th", "td"])]
    
    def col_idx(name):
        for i, h in enumerate(header_cells):
            if name in h:
                return i
        return None

    date_i  = col_idx("DATE") or 0
    lp95_i  = col_idx("LP 95") or col_idx("95")
    lp92_i  = col_idx("LP 92") or col_idx("92")
    lad_i   = col_idx("LAD")
    lsd_i   = col_idx("LSD")
    lk_i    = col_idx("LK")

    records = []
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 2:
            continue

        parsed_date = _parse_date(cells[date_i]) if date_i is not None else None
        if not parsed_date:
            continue

        def safe_get(idx):
            if idx is None or idx >= len(cells):
                return None
            return _parse_price(cells[idx])

        records.append({
            "date":  parsed_date,
            "lp_95": safe_get(lp95_i),
            "lp_92": safe_get(lp92_i),
            "lad":   safe_get(lad_i),
            "lsd":   safe_get(lsd_i),
            "lk":    safe_get(lk_i),
        })

    return pd.DataFrame(records)


def save_fuel_prices(df: pd.DataFrame, engine) -> int:
    """Upsert fuel prices into DB. Returns inserted row count."""
    if df.empty:
        print("No fuel price data to save.")
        return 0

    with engine.begin() as conn:
        _create_table(conn)
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO fuel_prices (date, lp_95, lp_92, lad, lsd, lk, source)
                VALUES (:date, :lp_95, :lp_92, :lad, :lsd, :lk, 'ceypetco')
                ON CONFLICT (date) DO UPDATE
                    SET lp_95  = EXCLUDED.lp_95,
                        lp_92  = EXCLUDED.lp_92,
                        lad    = EXCLUDED.lad,
                        lsd    = EXCLUDED.lsd,
                        lk     = EXCLUDED.lk,
                        source = EXCLUDED.source
            """), dict(row))

    return len(df)


def get_latest_fuel_prices(engine) -> dict:
    """Returns the most recent fuel prices as a dict for use in inference."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT lp_95, lp_92, lad, lsd, lk
            FROM fuel_prices ORDER BY date DESC LIMIT 1
        """)).fetchone()
    if not row:
        return {}
    return {
        "LP 95": float(row[0]) if row[0] else None,
        "LP 92": float(row[1]) if row[1] else None,
        "LAD":   float(row[2]) if row[2] else None,
        "LSD":   float(row[3]) if row[3] else None,
        "LK":    float(row[4]) if row[4] else None,
    }


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    engine = create_engine(DATABASE_URL)

    print("Scraping Ceypetco historical fuel prices...")
    df = scrape_fuel_prices()
    print(f"Found {len(df)} fuel price records. Latest: {df['date'].max()}")

    count = save_fuel_prices(df, engine)
    print(f"Saved {count} records to fuel_prices table.")


if __name__ == "__main__":
    main()
