#!/usr/bin/env python3
"""
Test script to verify the fish price scraper is working correctly.
Run this locally before relying on GitHub Actions.
"""

import os
import sys
from datetime import date, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.scraper import download_cbsl_report, extract_balaya_peliyagoda_today

def test_scraper():
    """Test the scraper with different dates."""
    
    print("="*70)
    print("FISH PRICE SCRAPER TEST")
    print("="*70)
    
    # Test dates
    test_dates = [
        date.today(),  # Today
        date.today() - timedelta(days=1),  # Yesterday
        date(2026, 4, 25),  # Known good date
    ]
    
    for target_date in test_dates:
        print(f"\n>>> Testing date: {target_date} ({target_date.strftime('%A')})")
        
        # Step 1: Download
        print("  Step 1: Downloading CBSL report...")
        pdf_path = download_cbsl_report(target_date)
        
        if not pdf_path:
            print("  ⚠ Could not download (normal if report not published)")
            continue
        
        # Step 2: Extract
        print("  Step 2: Extracting price...")
        price = extract_balaya_peliyagoda_today(pdf_path)
        
        if price:
            print(f"  ✓ SUCCESS: Rs. {price}")
        else:
            print(f"  ⚠ Could not extract price (marked N/A or not found)")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. If extraction was successful, the scraper is working")
    print("2. Ensure DATABASE_URL is set in GitHub Secrets")
    print("3. Verify the daily_scrape.yml workflow can run")

if __name__ == "__main__":
    test_scraper()
