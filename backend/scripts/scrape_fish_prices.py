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
    print("="*60)
    print("FISH PRICE SCRAPER")
    print("="*60)
    
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set in environment")
        sys.exit(1)

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
    except Exception as e:
        print(f"ERROR: Cannot connect to database: {e}")
        sys.exit(1)

    today = date.today()
    print(f"Target date: {today}")

    # 1. Download and Extract
    print(f"\n>>> Downloading CBSL report for {today}...")
    pdf_path = download_cbsl_report(today)
    
    if not pdf_path:
        print(f"⚠ Could not download CBSL report for {today}")
        print("  This is normal if the report isn't published yet (weekends/holidays)")
    else:
        print(f"✓ Downloaded: {pdf_path}")

    price = None
    if pdf_path:
        print(f"\n>>> Extracting Balaya price from Peliyagoda column...")
        try:
            price = extract_balaya_peliyagoda_today(pdf_path)
            if price:
                print(f"✓ Extracted price: Rs. {price}")
            else:
                print(f"⚠ Could not extract price from PDF (marked as N/A or not found)")
        except Exception as e:
            print(f"ERROR: Failed to extract price: {e}")
            price = None
    
    # 2. If no actual price, forward-fill from DB
    if price is None:
        print(f"\n>>> Forward-filling price from database...")
        try:
            with engine.connect() as conn:
                last_price_row = conn.execute(text("""
                    SELECT price FROM price_history 
                    WHERE fish = :fish AND location = :location 
                    ORDER BY date DESC LIMIT 1
                """), {"fish": FISH, "location": LOCATION}).fetchone()
                
                if last_price_row:
                    price = float(last_price_row[0])
                    print(f"✓ Forward-filled from last available price: Rs. {price}")
                else:
                    print(f"ERROR: No historical price found to forward-fill")
                    sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to get forward-fill price: {e}")
            sys.exit(1)

    # 3. Save to DB
    print(f"\n>>> Saving to database...")
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO price_history (date, price, location, fish, source)
                VALUES (:date, :price, :location, :fish, 'github_actions')
                ON CONFLICT (date, location, fish) DO UPDATE
                SET price = EXCLUDED.price, source = EXCLUDED.source
            """), {"date": today, "price": price, "location": LOCATION, "fish": FISH})
        
        print(f"✓ Successfully saved price for {today}: Rs. {price}")
        print("="*60)
        print("SCRAPE COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"ERROR: Failed to save to database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
