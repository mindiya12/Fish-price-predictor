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
    print("="*60)
    print("FISH PRICE SCRAPER")
    print("="*60)
    
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not set in environment")
        sys.exit(1)

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[SUCCESS] Database connection successful")
    except Exception as e:
        print(f"[ERROR] Cannot connect to database: {e}")
        sys.exit(1)

    # Try today, then yesterday if today fails
    target_dates = [date.today(), date.today() - timedelta(days=1)]
    
    pdf_path = None
    scraped_date = None
    price = None
    
    for target_date in target_dates:
        print(f"\n>>> Attempting to scrape for {target_date}...")
        pdf_path = download_cbsl_report(target_date)
        
        if pdf_path:
            print(f"[SUCCESS] Downloaded: {pdf_path}")
            try:
                price = extract_balaya_peliyagoda_today(pdf_path)
                if price:
                    scraped_date = target_date
                    print(f"[SUCCESS] Extracted price for {scraped_date}: Rs. {price}")
                    break
                else:
                    print(f"[INFO] Could not extract price from {target_date} report (likely N/A)")
            except Exception as e:
                print(f"[ERROR] Failed to extract price from {target_date}: {e}")
        else:
            print(f"[INFO] CBSL report for {target_date} not available yet.")

    # If no actual price found, forward-fill from DB
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
                    print(f"[INFO] Forward-filled from last available price: Rs. {price}")
                else:
                    print(f"[ERROR] No historical price found to forward-fill")
                    sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to get forward-fill price: {e}")
            sys.exit(1)

    # Save to DB (using target date, not necessarily today if we scraped yesterday's report)
    # Actually, for the "daily update", we usually want to record it for 'today' 
    # but we should use the scraped date if we want the history to be accurate.
    # The existing logic uses 'today' for the DB entry date.
    
    save_date = date.today()
    print(f"\n>>> Saving to database for {save_date}...")
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO price_history (date, price, location, fish, source)
                VALUES (:date, :price, :location, :fish, 'github_actions')
                ON CONFLICT (date, location, fish) DO UPDATE
                SET price = EXCLUDED.price, source = EXCLUDED.source
            """), {"date": save_date, "price": price, "location": LOCATION, "fish": FISH})
        
        print(f"[SUCCESS] Saved price for {save_date}: Rs. {price}")
        print("="*60)
        print("SCRAPE COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        print(f"[ERROR] Failed to save to database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
