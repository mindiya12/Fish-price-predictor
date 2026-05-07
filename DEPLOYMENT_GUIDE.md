# 🐟 Fish Price Predictor - Deployment & Maintenance Guide

## Current Setup Status

### ✅ What's Working
- **Frontend:** Deployed on Vercel (https://fish-price-predictor.vercel.app/)
- **Backend:** Deployed on Fly.io (fish-price-predictor.fly.dev)
- **Database:** Supabase PostgreSQL
- **Frontend Code:** Auto-deploys when code is pushed

### ⚠️ What Needs Configuration
- **Daily Data Collection:** GitHub Actions workflow configured but needs secrets set
- **Model Retraining:** Part of daily workflow
- **Backend Updates:** Need to verify deployment after scraper runs

---

## 🔧 CRITICAL SETUP STEPS

### Step 1: Set GitHub Secrets (REQUIRED FOR AUTOMATION)

Your GitHub Actions workflows won't run without these secrets:

**Go to:** GitHub Repo → Settings → Secrets and Variables → Actions

**Add Secret #1: DATABASE_URL**
- **Name:** `DATABASE_URL`
- **Value:** Your Supabase connection string
  ```
  postgresql://postgres.XXXXXXXXXXXXX:XXXXXXXXXXXXXXX@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres
  ```
- Find this in: Supabase Dashboard → Project Settings → Database → Connection String

**Add Secret #2: FLY_API_TOKEN**
- **Name:** `FLY_API_TOKEN`
- **Value:** Your Fly.io API token
  ```
  flyctl auth token
  ```

**Verify:** GitHub → Actions tab should show green checkmarks for past runs

---

## 📋 Daily Workflow (Automated at 5 AM Sri Lanka Time)

The daily_scrape.yml workflow does this automatically:

```
23:30 UTC (5:00 AM SLT) → Triggered Daily
    ↓
[1] Scrape Weather Data (Open-Meteo)
[2] Scrape Fuel Prices  
[3] Scrape Fish Prices from CBSL (https://www.cbsl.gov.lk/...)
[4] Retrain XGBoost Models
[5] Commit updated models to GitHub
[6] Trigger Fly.io backend deployment
```

---

## 🧪 Testing the Setup

### Test 1: Verify Scraper Works

```bash
cd backend

# Set your database URL
export DATABASE_URL="postgresql://..."

# Run the scraper
python scripts/scrape_fish_prices.py
```

You should see:
```
============================================================
FISH PRICE SCRAPER
============================================================
>>> Downloading CBSL report for 2026-05-07...
  Downloading from: https://www.cbsl.gov.lk/sites/...
  Response status: 200
  Content-Type: application/pdf
  Saved: /tmp/cbsl_price_reports/price_report_20260507_e.pdf (...)

>>> Extracting Balaya price from Peliyagoda column...
  PDF opened successfully (2 pages)
  Extracted 150+ words from page 2
  Found 'Balaya' at y=...
  Assembled raw price: '1050.00'
  ✓ Parsed price: Rs. 1050.0

>>> Saving to database...
✓ Successfully saved price for 2026-05-07: Rs. 1050.0
============================================================
```

### Test 2: Check Database Status

```bash
export DATABASE_URL="postgresql://..."
python check_database.py
```

This shows:
- Last 10 prices in the database
- How many days behind we are
- Data quality metrics

### Test 3: Manually Trigger Workflow

1. Go to GitHub Repo → **Actions** tab
2. Select **"Daily Fish Price Scrape & Retrain"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Monitor the logs in real-time

---

## 🔍 Troubleshooting

### ❌ Issue: Prices stuck on old date

**Diagnosis:**
```bash
python check_database.py
# Shows: "Data is X day(s) behind"
```

**Solutions:**
1. **Check if it's a weekend:** Prices won't update Saturday-Sunday
2. **Check if CBSL published the report:** Visit https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report
3. **Check GitHub Actions:** Actions → Daily Fish Price Scrape & Retrain
   - If no recent run: Secrets not set or workflow disabled
   - If failed run: Click to see error logs

### ❌ Issue: Workflow hasn't run in days

**Check:**
1. GitHub → Settings → Secrets → Verify `DATABASE_URL` exists ✓
2. GitHub → Actions → Enable workflows if disabled
3. GitHub → Actions → "Daily Fish Price Scrape & Retrain" → Manual trigger test

**If still failing:**
- Click failed run to see logs
- Look for error like: `ERROR: DATABASE_URL not set`
- Ensure secret is spelled exactly: `DATABASE_URL`

### ❌ Issue: Prices are all the same

**Possible causes:**
- CBSL website marked price as N/A (holiday/weekend)
- Scraper is forward-filling from last good price (normal behavior)
- PDF extraction failed

**Check logs:**
```bash
# In GitHub Actions, look for output like:
"Price marked as N/A"
"Forward-filled from last available price: Rs. 950"
```

---

## 📊 How Data Flows

```
CBSL Website (Daily 5 AM SLT)
    ↓ (PDF Scraper downloads)
GitHub Actions
    ↓ (Extracts data)
Supabase Database
    ↓ (Stored)
Your Fly.io Backend ← Also retrains ML models
    ↓ (API endpoints)
Vercel Frontend ← Fetches data
    ↓
Your Users See Live Prices
```

---

## 📝 Monitoring Checklist

Run these weekly to ensure everything works:

**Monday:**
```bash
python check_database.py
# Should show data updated Friday
```

**After Manual Trigger:**
```bash
# 1. Go to GitHub Actions
# 2. Click latest run
# 3. Expand each step - should see ✓ checkmarks
# 4. No red errors
```

**Monthly:**
```bash
# Test scraper locally
export DATABASE_URL="..."
python test_scraper.py
# Should show extraction for multiple dates
```

---

## 🚀 Emergency: Manually Update Price

If scraper fails but you have the price:

```bash
cd backend

# Set database URL
export DATABASE_URL="postgresql://..."

# Create a quick update script
python3 << 'EOF'
from datetime import date
from sqlalchemy import create_engine, text
import os

db_url = os.environ.get("DATABASE_URL")
engine = create_engine(db_url)

# Update with your price
today = date.today()
price = 1050.00  # Update this

with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO price_history (date, price, location, fish, source)
        VALUES (:date, :price, :location, :fish, :source)
        ON CONFLICT (date, location, fish) DO UPDATE
        SET price = EXCLUDED.price
    """), {
        "date": today,
        "price": price,
        "location": "peliyagoda",
        "fish": "balaya",
        "source": "manual_update"
    })

print(f"Updated {today} with price Rs. {price}")
EOF
```

---

## 📞 Support

If something isn't working:

1. **Check Logs First:**
   - GitHub Actions → View failed workflow
   - Fly.io → View application logs

2. **Run Diagnostics:**
   ```bash
   python check_database.py
   python test_scraper.py
   ```

3. **Common Fixes:**
   - Restart Fly.io: `flyctl restart`
   - Redeploy: `git push origin main`
   - Manual workflow trigger: GitHub Actions → Run workflow

---

## 📅 Scheduled Tasks

| Time | Task | Frequency |
|------|------|-----------|
| 23:30 UTC | Scrape data & retrain | Daily |
| 5 AM SLT | ↑ (same as above) | Daily |
| On push | Deploy frontend | Per push |
| On workflow | Deploy backend | After scraper |

---

## ✅ Deployment Verification

After setup, verify:

```bash
# 1. Frontend loads
curl https://fish-price-predictor.vercel.app/history
# Should return HTML page

# 2. Backend responds
curl https://fish-price-predictor.fly.dev/api/health
# Should return {"status": "ok"}

# 3. Database has recent data
python check_database.py
# Should show data updated in last 2 days
```

---

**Last Updated:** May 7, 2026
**Status:** Ready for daily automated updates
