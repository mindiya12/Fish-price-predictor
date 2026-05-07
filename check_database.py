#!/usr/bin/env python3
"""
Database monitoring script to check if data is being updated correctly.
Use this to debug why prices aren't updating.
"""

import os
import sys
from datetime import date, timedelta
from sqlalchemy import create_engine, text

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")

def check_database():
    """Check database state and report issues."""
    
    print("="*70)
    print("DATABASE STATE MONITOR")
    print("="*70)
    
    if not DATABASE_URL:
        print("\n❌ ERROR: DATABASE_URL not set in environment")
        print("   Set it with: export DATABASE_URL='postgresql://...'")
        return False
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("\n✓ Database connection successful")
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to database")
        print(f"   {e}")
        return False
    
    # Check price_history table
    print("\n" + "-"*70)
    print("PRICE HISTORY STATUS")
    print("-"*70)
    
    try:
        with engine.connect() as conn:
            # Total rows
            total = conn.execute(
                text("SELECT COUNT(*) as cnt FROM price_history WHERE fish='balaya' AND location='peliyagoda'")
            ).scalar()
            print(f"Total historical prices: {total}")
            
            # Last 10 prices
            print("\nLast 10 prices:")
            rows = conn.execute(text("""
                SELECT date, price, source 
                FROM price_history 
                WHERE fish='balaya' AND location='peliyagoda'
                ORDER BY date DESC 
                LIMIT 10
            """)).fetchall()
            
            for i, (dt, price, source) in enumerate(rows):
                days_ago = (date.today() - dt.date()).days
                status = "✓" if days_ago == 0 else "⚠" if days_ago <= 2 else "-"
                print(f"  {status} {dt.date()} ({days_ago}d ago): Rs. {price:,.0f} [{source}]")
            
            # Check for gaps
            print("\nData gap check:")
            last_date = rows[0][0].date() if rows else None
            today = date.today()
            
            if last_date and last_date < today:
                gap_days = (today - last_date).days
                print(f"  ⚠ Data is {gap_days} day(s) behind (last: {last_date}, today: {today})")
                if gap_days <= 2:
                    print("    This is normal for weekends/holidays")
                else:
                    print("    ⚠ Check if scraper is running properly")
            elif last_date and last_date == today:
                print(f"  ✓ Data is current (updated today)")
            
            # Check for duplicates
            print("\nData quality check:")
            dupes = conn.execute(text("""
                SELECT date, COUNT(*) as cnt 
                FROM price_history 
                WHERE fish='balaya' AND location='peliyagoda'
                GROUP BY date 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if dupes:
                print(f"  ⚠ Found {len(dupes)} dates with duplicate entries")
                for dt, cnt in dupes[:5]:
                    print(f"    {dt.date()}: {cnt} entries")
            else:
                print(f"  ✓ No duplicate entries")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    
    # Check for monotonic prices (sign of bad data)
    print("\n" + "-"*70)
    print("DATA PATTERN ANALYSIS")
    print("-"*70)
    
    try:
        with engine.connect() as conn:
            recent = conn.execute(text("""
                SELECT price 
                FROM price_history 
                WHERE fish='balaya' AND location='peliyagoda'
                ORDER BY date DESC 
                LIMIT 30
            """)).fetchall()
            
            prices = [r[0] for r in recent]
            
            if len(prices) >= 2:
                # Check variance
                import statistics
                variance = statistics.variance(prices)
                stdev = statistics.stdev(prices)
                mean = statistics.mean(prices)
                cv = (stdev / mean * 100) if mean > 0 else 0
                
                print(f"Last 30 days:")
                print(f"  Mean: Rs. {mean:,.0f}")
                print(f"  Stdev: Rs. {stdev:,.0f}")
                print(f"  Coeff. of Variation: {cv:.1f}%")
                
                if cv < 1:
                    print(f"  ⚠ Very low variance - prices might not be changing correctly")
                else:
                    print(f"  ✓ Healthy price variance")
    
    except Exception as e:
        print(f"Could not analyze patterns: {e}")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    print("""
1. If data is current (updated today):
   ✓ The scraper is working correctly
   
2. If data is 1-2 days old:
   - Check if it's a weekend/holiday (normal)
   - Or wait for the next daily run (5 AM Sri Lanka time)
   
3. If data is 3+ days old:
   ⚠ The scraper may not be running
   - Check GitHub Actions → Daily Fish Price Scrape & Retrain
   - Verify DATABASE_URL is set in GitHub Secrets
   - Check workflow logs for errors
   
4. If prices are all the same:
   ⚠ Data forward-filling is happening (weekend/no report)
   - This is normal on weekends
   - Check if CBSL published the report
""")

if __name__ == "__main__":
    check_database()
