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

def backfill():
    print("="*60)
    print("FISH PRICE BACKFILL SCRIPT")
    print("="*60)
    
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not set in environment")
        sys.exit(1)

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        print("[SUCCESS] Database connection successful")
    except Exception as e:
        print(f"[ERROR] Cannot connect to database: {e}")
        sys.exit(1)

    # Range: April 27th to May 6th (inclusive)
    start_date = date(2026, 4, 27)
    end_date = date(2026, 5, 6)
    
    current_date = start_date
    while current_date <= end_date:
        print(f"\n>>> Processing {current_date}...")
        
        pdf_path = download_cbsl_report(current_date)
        if not pdf_path:
            print(f"[INFO] Report not available for {current_date}")
        else:
            try:
                price = extract_balaya_peliyagoda_today(pdf_path)
                if price:
                    print(f"[SUCCESS] Extracted price for {current_date}: Rs. {price}")
                    
                    # Update DB
                    with engine.begin() as conn:
                        conn.execute(text("""
                            INSERT INTO price_history (date, price, location, fish, source)
                            VALUES (:date, :price, :location, :fish, 'backfill')
                            ON CONFLICT (date, location, fish) DO UPDATE
                            SET price = EXCLUDED.price, source = EXCLUDED.source
                        """), {"date": current_date, "price": price, "location": LOCATION, "fish": FISH})
                    print(f"[SUCCESS] Updated database for {current_date}")
                else:
                    print(f"[INFO] Could not extract price for {current_date} (likely N/A)")
            except Exception as e:
                print(f"[ERROR] Failed to process {current_date}: {e}")
        
        current_date += timedelta(days=1)

    print("\n" + "="*60)
    print("BACKFILL COMPLETED")
    print("="*60)

if __name__ == "__main__":
    backfill()
