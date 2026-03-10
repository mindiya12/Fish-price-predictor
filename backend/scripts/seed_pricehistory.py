import os
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
# Point to the new Excel file
EXCEL_PATH = os.environ.get("EXCEL_PATH", "/data/historical_data.xlsx")

FISH = os.environ.get("FISH", "balaya")
LOCATION = os.environ.get("LOCATION", "peliyagoda")
SOURCE = os.environ.get("SOURCE", "seed_excel")

def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    # Read the Excel file
    try:
        df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel file at {EXCEL_PATH}. Error: {e}")

    # Standardize column names to lowercase to make it easy to find "date" and "price"
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "date" not in df.columns or "price" not in df.columns:
        raise RuntimeError(f"Excel file must contain 'date' and 'price' columns. Found: {df.columns.tolist()}")

    df = df[["date", "price"]].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna()

    engine = create_engine(DATABASE_URL)

    insert_q = text("""
        INSERT INTO price_history (date, price, location, fish, source)
        VALUES (:date, :price, :location, :fish, :source)
        ON CONFLICT (date, location, fish) DO NOTHING
    """)

    with engine.begin() as conn:
        for row in df.itertuples(index=False):
            conn.execute(insert_q, {
                "date": row.date,
                "price": float(row.price),
                "location": LOCATION,
                "fish": FISH,
                "source": SOURCE,
            })

    print(f"Seeded {len(df)} rows from Excel (duplicates skipped).")

if __name__ == "__main__":
    main()
