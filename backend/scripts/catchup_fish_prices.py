import os
import sys
from datetime import date, timedelta
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
    
    # Get the latest date in the database
    with engine.connect() as conn:
        latest_row = conn.execute(text("""
            SELECT MAX(date) FROM price_history 
            WHERE fish = :fish AND location = :location
        """), {"fish": FISH, "location": LOCATION}).fetchone()
        
    start_date = latest_row[0] if latest_row and latest_row[0] else date(2026, 3, 26)
    
    if start_date:
        start_date += timedelta(days=1)
        
    end_date = date.today()
    
    if start_date > end_date:
        print("Database is already up to date with fish prices.")
        return
        
    print(f"Catching up fish prices from {start_date} to {end_date}...")
    
    current_date = start_date
    last_known_price = None
    
    # Get last known price from DB for forward-filling
    with engine.connect() as conn:
        last_price_row = conn.execute(text("""
            SELECT price FROM price_history 
            WHERE fish = :fish AND location = :location AND date < :date
            ORDER BY date DESC LIMIT 1
        """), {"fish": FISH, "location": LOCATION, "date": start_date}).fetchone()
        
        if last_price_row:
            last_known_price = float(last_price_row[0])

    while current_date <= end_date:
        print(f"[{current_date}] Fetching...")
        pdf_path = download_cbsl_report(current_date)
        price = None
        
        if pdf_path:
            price = extract_balaya_peliyagoda_today(pdf_path)
        
        if price is None:
            print(f"  -> Could not extract. Forward-filling: {last_known_price}")
            price = last_known_price
        else:
            last_known_price = price
            print(f"  -> Extracted: {price}")
            
        if price is not None:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO price_history (date, price, location, fish, source)
                    VALUES (:date, :price, :location, :fish, 'catchup_script')
                    ON CONFLICT (date, location, fish) DO UPDATE
                    SET price = EXCLUDED.price, source = EXCLUDED.source
                """), {"date": current_date, "price": price, "location": LOCATION, "fish": FISH})
                
        current_date += timedelta(days=1)
    
    print("Catch-up complete!")

if __name__ == "__main__":
    main()
