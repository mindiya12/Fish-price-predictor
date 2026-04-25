import os
import sys
from datetime import date
from sqlalchemy import create_engine, text

# Add parent directory to path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.scraper import download_cbsl_report, extract_balaya_peliyagoda_today

DATABASE_URL = os.environ.get("DATABASE_URL")
FISH = "balaya"
LOCATION = "peliyagoda"

def main():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    engine = create_engine(DATABASE_URL)
    today = date.today()
    print(f"Starting fish price scrape for {today}...")

    # 1. Download and Extract
    pdf_path = download_cbsl_report(today)
    price = None
    if pdf_path:
        price = extract_balaya_peliyagoda_today(pdf_path)
    
    if price is None:
        print(f"Warning: Could not extract price for {today}. CBSL report might not be out yet or it is a holiday.")
        # We will forward-fill from the DB for the purpose of the pipeline
        with engine.connect() as conn:
            last_price_row = conn.execute(text("""
                SELECT price FROM price_history 
                WHERE fish = :fish AND location = :location 
                ORDER BY date DESC LIMIT 1
            """), {"fish": FISH, "location": LOCATION}).fetchone()
            if last_price_row:
                price = float(last_price_row[0])
                print(f"Forward-filling price: {price}")
            else:
                print("Error: No historical price found to forward-fill.")
                sys.exit(1)

    # 2. Save to DB
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO price_history (date, price, location, fish, source)
            VALUES (:date, :price, :location, :fish, 'github_actions')
            ON CONFLICT (date, location, fish) DO UPDATE
            SET price = EXCLUDED.price, source = EXCLUDED.source
        """), {"date": today, "price": price, "location": LOCATION, "fish": FISH})
    
    print(f"Successfully updated price_history for {today} with price {price}")

if __name__ == "__main__":
    main()
