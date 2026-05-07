# GitHub Actions Setup Guide

## Required GitHub Secrets

Your workflows require the following secrets to be set in GitHub:

### 1. DATABASE_URL
**Location:** GitHub Repo → Settings → Secrets and Variables → Actions → New Repository Secret

**Name:** `DATABASE_URL`
**Value:** Your Supabase connection string
```
postgresql://username:password@host:port/database
```

**Example:**
```
postgresql://postgres.XXXXXXXXXXXXX:XXXXXXXXXXXXXXX@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres
```

### 2. FLY_API_TOKEN
**Name:** `FLY_API_TOKEN`
**Value:** Your Fly.io API token (from `flyctl auth token`)

---

## Workflow Files

### daily_scrape.yml (Automated Daily Updates)
- **Trigger:** Automatically at 23:30 UTC (5:00 AM Sri Lanka Time)
- **Can also trigger manually:** GitHub → Actions → Daily Fish Price Scrape & Retrain → Run workflow
- **Actions:**
  1. Scrapes fish prices from CBSL website
  2. Downloads weather data from Open-Meteo
  3. Retrains ML models
  4. Commits model updates
  5. Triggers backend deployment to Fly.io

### deploy-backend.yml
- **Trigger:** Automatically when backend code changes
- **Or manually triggered by daily_scrape.yml**
- **Action:** Deploys updated backend to Fly.io

### ci.yml
- **Trigger:** On every push to main
- **Action:** Runs frontend linting and tests

---

## Troubleshooting

### Workflow doesn't run
1. Check GitHub Secrets are set: Settings → Secrets and Variables → Actions
2. Verify DATABASE_URL and FLY_API_TOKEN exist
3. Check workflow file syntax (YAML indentation)
4. View workflow runs: GitHub → Actions tab

### Workflow runs but fails
1. Click the failed run to see logs
2. Look for error messages
3. Check if DATABASE_URL is correct (can connect to Supabase)
4. Verify the FLY_API_TOKEN is still valid

### Data not updating
1. Check if daily_scrape.yml ran: Actions tab
2. Verify no errors in the run logs
3. Check if CBSL website has published the report
4. Check database connection

---

## Manual Testing

### Test Scraper Locally
```bash
cd backend

# Set database URL
export DATABASE_URL="postgresql://..."

# Run scraper
python scripts/scrape_fish_prices.py

# You should see detailed output like:
# >>> Downloading CBSL report for 2026-05-07...
# ✓ Extracted price: Rs. 1050
# ✓ Successfully saved price
```

### Check Workflow Run Status
1. Go to GitHub → Actions tab
2. Click on the latest "Daily Fish Price Scrape & Retrain" run
3. Expand each step to see logs

---

## Emergency Manual Trigger

If the daily workflow fails, manually trigger it:

1. Go to GitHub Repository → Actions tab
2. Select "Daily Fish Price Scrape & Retrain" workflow
3. Click "Run workflow" → "Run workflow"
4. Monitor logs for errors
