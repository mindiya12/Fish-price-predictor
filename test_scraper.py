#!/usr/bin/env python3
import os
import sys
from datetime import date, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.scraper import download_cbsl_report, extract_balaya_peliyagoda_today

def test_scraper():
    print("="*70)
    print("FISH PRICE SCRAPER TEST")
    print("="*70)
    
    # Test dates
    test_dates = [
        date.today(),
        date.today() - timedelta(days=1),
        date(2026, 4, 27),
    ]
    
    for target_date in test_dates:
        print(f"\n>>> Testing date: {target_date} ({target_date.strftime('%A')})")
        
        pdf_path = download_cbsl_report(target_date)
        
        if not pdf_path:
            print("  [WARNING] Could not download")
            continue
        
        price = extract_balaya_peliyagoda_today(pdf_path)
        
        if price:
            print(f"  [SUCCESS] Rs. {price}")
        else:
            print("  [WARNING] Could not extract price")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_scraper()
