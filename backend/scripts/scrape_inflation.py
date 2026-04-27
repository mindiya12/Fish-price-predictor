"""
Inflation Scraper - CBSL CCPI Press Releases
=============================================
Scrapes monthly inflation (CCPI-based) from CBSL press release PDFs
and stores them in the `inflation_data` table.

Each monthly PDF contains a table with the headline inflation figure.
This scraper discovers the latest PDF URL from the CBSL page, downloads
the PDF, and extracts the CCPI headline inflation value.

Feature mapped: Inflation_Rate
"""

import os
import re
import requests
import pdfplumber
from bs4 import BeautifulSoup
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, text
import io

DATABASE_URL = os.environ.get("DATABASE_URL")

CBSL_PAGE_URL = "https://www.cbsl.gov.lk/en/measures-of-consumer-price-inflation"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# PDF URL template – constructed from press release naming convention:
# press_{YYYYMMDD}_inflation_in_{month_name}_{YYYY}_ccpi_e.pdf
# We scrape the page for links matching this pattern.
PDF_LINK_PATTERN = re.compile(r"press_\d{8}_inflation.*?ccpi.*?\.pdf", re.IGNORECASE)


def _create_table(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS inflation_data (
            id              SERIAL PRIMARY KEY,
            reference_month DATE NOT NULL UNIQUE,
            ccpi_headline   NUMERIC,
            ccpi_food       NUMERIC,
            ccpi_non_food   NUMERIC,
            source_pdf      TEXT,
            created_at      TIMESTAMP DEFAULT NOW()
        );
    """))


def _get_pdf_links() -> list[str]:
    """Scrape the CBSL page and return list of CCPI inflation PDF URLs."""
    resp = requests.get(CBSL_PAGE_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if PDF_LINK_PATTERN.search(href):
            if not href.startswith("http"):
                href = "https://www.cbsl.gov.lk" + href
            links.append(href)
    
    # Deduplicate while preserving order (page sometimes repeats links)
    seen = set()
    uniq: list[str] = []
    for u in links:
        if u in seen:
            continue
        seen.add(u)
        uniq.append(u)
    return uniq


def _extract_month_from_url(pdf_url: str) -> date | None:
    """Extract reference month (first day of month) from PDF url."""
    # Filename pattern: press_20260227_inflation_in_february_2026_ccpi_e.pdf
    m = re.search(r"inflation_in_([a-z]+)_(\d{4})", pdf_url, re.IGNORECASE)
    if m:
        month_name, year = m.group(1), m.group(2)
        try:
            return datetime.strptime(f"1 {month_name} {year}", "%d %B %Y").date()
        except ValueError:
            pass
    return None


def _parse_ccpi_from_pdf(pdf_bytes: bytes) -> dict:
    """
    Extract CCPI headline inflation from the PDF.
    Returns dict with keys: ccpi_headline, ccpi_food, ccpi_non_food
    """
    result = {"ccpi_headline": None, "ccpi_food": None, "ccpi_non_food": None}
    
    def _safe_float(val: str) -> float | None:
        try:
            x = float(val)
        except Exception:
            return None
        # Sanity bounds for inflation rates (%). Avoid capturing years like 2026.
        if x < -100 or x > 100:
            return None
        return x

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                
                # Look for "Headline Inflation" percentage figure
                # Require a % sign after the number to avoid matching years (e.g., 2026)
                headline_match = re.search(
                    r"headline\s+inflation[^%]{0,60}?(-?\d+(?:\.\d+)?)\s*%",
                    text, re.IGNORECASE
                )
                if headline_match:
                    result["ccpi_headline"] = _safe_float(headline_match.group(1))
                
                # Look for "Food Inflation"
                food_match = re.search(
                    r"food\s+inflation[^%]{0,60}?(-?\d+(?:\.\d+)?)\s*%",
                    text, re.IGNORECASE
                )
                if food_match:
                    result["ccpi_food"] = _safe_float(food_match.group(1))

                # Non-food
                non_food_match = re.search(
                    r"non.food\s+inflation[^%]{0,60}?(-?\d+(?:\.\d+)?)\s*%",
                    text, re.IGNORECASE
                )
                if non_food_match:
                    result["ccpi_non_food"] = _safe_float(non_food_match.group(1))
                
                # Break early if we have what we need
                if result["ccpi_headline"] is not None:
                    break
    except Exception as e:
        print(f"Error parsing PDF: {e}")
    
    return result


def scrape_and_store_inflation(engine, max_records: int = 120):
    """
    Scrape CBSL inflation PDFs and store in DB.
    max_records limits backfill to N months (default 10 years = 120 months).
    """
    print("Fetching CBSL inflation PDF links...")
    pdf_links = _get_pdf_links()
    
    if not pdf_links:
        print("No PDF links found. Page may require JavaScript rendering.")
        return 0
    
    print(f"Found {len(pdf_links)} inflation PDFs.")
    
    with engine.begin() as conn:
        _create_table(conn)
    
    inserted = 0
    for url in pdf_links[:max_records]:
        ref_month = _extract_month_from_url(url)
        if not ref_month:
            print(f"Could not parse month from: {url}")
            continue
        
        print(f"Processing: {ref_month.strftime('%B %Y')} — {url}")
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                print(f"  Failed to download PDF (status {r.status_code}), skipping.")
                continue
            
            metrics = _parse_ccpi_from_pdf(r.content)
            
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO inflation_data (reference_month, ccpi_headline, ccpi_food, ccpi_non_food, source_pdf)
                    VALUES (:month, :headline, :food, :non_food, :pdf_url)
                    ON CONFLICT (reference_month) DO UPDATE
                        SET ccpi_headline = EXCLUDED.ccpi_headline,
                            ccpi_food     = EXCLUDED.ccpi_food,
                            ccpi_non_food = EXCLUDED.ccpi_non_food,
                            source_pdf    = EXCLUDED.source_pdf
                """), {
                    "month":    ref_month,
                    "headline": metrics["ccpi_headline"],
                    "food":     metrics["ccpi_food"],
                    "non_food": metrics["ccpi_non_food"],
                    "pdf_url":  url,
                })
            
            print(f"  Saved: Headline={metrics['ccpi_headline']}%")
            inserted += 1
        
        except Exception as e:
            print(f"  Error processing {url}: {e}")
    
    return inserted


def get_latest_inflation(engine) -> float | None:
    """Returns the most recent CCPI headline inflation value for feature use."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT ccpi_headline FROM inflation_data
            ORDER BY reference_month DESC LIMIT 1
        """)).fetchone()
    
    return float(row[0]) if row and row[0] is not None else None


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    
    engine = create_engine(DATABASE_URL)
    count = scrape_and_store_inflation(engine)
    print(f"Stored {count} monthly inflation records.")


if __name__ == "__main__":
    main()
