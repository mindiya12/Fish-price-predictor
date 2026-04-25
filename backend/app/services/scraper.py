import os
import requests
import pdfplumber
import re
from datetime import date, timedelta
from typing import Optional, Dict, Any

# ── Configuration ─────────────────────────────────────────────────────────────
PDF_DIR = "/tmp/cbsl_price_reports"
os.makedirs(PDF_DIR, exist_ok=True)

URL_TEMPLATE = (
    "https://www.cbsl.gov.lk/sites/default/files/"
    "cbslweb_documents/statistics/pricerpt/price_report_{yyyymmdd}_e.pdf"
)
TIMEOUT = 60

# X-coordinate band for the "Peliyagoda Today" column (wholesale)
PELIYGODA_TODAY_X_MIN = 198
PELIYGODA_TODAY_X_MAX = 235
Y_TOL = 5

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_price(text: str) -> Optional[float]:
    """Convert a raw word fragment like '1', ',000.00' to float."""
    text = text.strip().replace(',', '').replace(' ', '')
    if text.lower() in ('n.a.', 'na', ''):
        return None
    try:
        return float(text)
    except ValueError:
        return None

def download_cbsl_report(target_date: date) -> Optional[str]:
    """Downloads the CBSL report for the specific date."""
    yyyymmdd = target_date.strftime("%Y%m%d")
    url = URL_TEMPLATE.format(yyyymmdd=yyyymmdd)
    pdf_path = os.path.join(PDF_DIR, f"price_report_{yyyymmdd}_e.pdf")

    # If already downloaded today, reuse it
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        return pdf_path

    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200 and r.headers.get("content-type", "").lower().find("pdf") != -1:
            with open(pdf_path, "wb") as f:
                f.write(r.content)
            return pdf_path
    except Exception as e:
        print(f"Error downloading CBSL report: {e}")
        
    return None

def extract_balaya_peliyagoda_today(pdf_path: str) -> Optional[float]:
    """
    Use raw word positions to extract Balaya Peliyagoda Today wholesale price.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 2:
                return None
            words = pdf.pages[1].extract_words()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

    # Step 1: find 'Balaya' in the fish section
    balaya_y = None
    for w in words:
        if w['text'] == 'Balaya' and w['top'] > 550:
            balaya_y = w['top']
            break

    if balaya_y is None:
        return None

    # Step 2: collect price fragments on the same row in Peliyagoda-Today band
    fragments = []
    for w in words:
        if abs(w['top'] - balaya_y) <= Y_TOL:
            x_mid = (w['x0'] + w['x1']) / 2
            if PELIYGODA_TODAY_X_MIN <= x_mid <= PELIYGODA_TODAY_X_MAX:
                fragments.append((w['x0'], w['text']))

    if not fragments:
        return None

    fragments.sort(key=lambda t: t[0])
    raw = ''.join(t[1] for t in fragments)

    if 'n' in raw.lower() or 'a' in raw.lower():
        return None

    return parse_price(raw)


def fetch_open_meteo_weather(target_date: date) -> Dict[str, Any]:
    """
    Fetches real historical/current weather from Open-Meteo for the 5 coastal cities.
    We fetch data for target_date.
    """
    # Sri Lanka coastal coordinates
    locations = {
        "Matara": {"lat": 5.9485, "lon": 80.5353},
        "Galle": {"lat": 6.0367, "lon": 80.2170},
        "Negombo": {"lat": 7.2008, "lon": 79.8737},
        "Kalutara": {"lat": 6.5854, "lon": 79.9607},
        "Tangalla": {"lat": 6.0240, "lon": 80.7941}
    }
    
    date_str = target_date.strftime("%Y-%m-%d")
    weather_data = {}
    
    for city, coords in locations.items():
        # Open-Meteo Historical API is best for getting specific past days reliably
        url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={coords['lat']}&longitude={coords['lon']}"
            f"&start_date={date_str}&end_date={date_str}"
            f"&daily=temperature_2m_mean,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max"
            f"&timezone=Asia%2FColombo"
        )
        
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                daily = data.get("daily", {})
                
                # Extract the 4 metrics, fallback to 0 if totally missing
                temp = daily.get("temperature_2m_mean", [26.0])[0]
                precip = daily.get("precipitation_sum", [0.0])[0]
                wind = daily.get("wind_speed_10m_max", [15.0])[0]
                gust = daily.get("wind_gusts_10m_max", [20.0])[0]
                
                # Handle nulls returned by API (sometimes happens for very recent days before archive is ready)
                weather_data[f"{city}_temp_mean_C"] = temp if temp is not None else 26.0
                weather_data[f"{city}_precip_mm"] = precip if precip is not None else 0.0
                weather_data[f"{city}_wind_max_kmh"] = wind if wind is not None else 15.0
                weather_data[f"{city}_gust_max_kmh"] = gust if gust is not None else 20.0
            else:
                # If archive fails, try the forecast API (works for today/recent days better sometimes)
                url_forecast = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={coords['lat']}&longitude={coords['lon']}"
                    f"&start_date={date_str}&end_date={date_str}"
                    f"&daily=temperature_2m_mean,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max"
                    f"&timezone=Asia%2FColombo"
                )
                r_forecast = requests.get(url_forecast, timeout=10)
                if r_forecast.status_code == 200:
                    data = r_forecast.json()
                    daily = data.get("daily", {})
                    weather_data[f"{city}_temp_mean_C"] = daily.get("temperature_2m_mean", [26.0])[0] or 26.0
                    weather_data[f"{city}_precip_mm"] = daily.get("precipitation_sum", [0.0])[0] or 0.0
                    weather_data[f"{city}_wind_max_kmh"] = daily.get("wind_speed_10m_max", [15.0])[0] or 15.0
                    weather_data[f"{city}_gust_max_kmh"] = daily.get("wind_gusts_10m_max", [20.0])[0] or 20.0
                else:
                    raise ValueError("Both Open-Meteo APIs failed")
                    
        except Exception as e:
            print(f"Error fetching weather for {city}: {e}")
            # Fallback defaults if API is totally down
            weather_data[f"{city}_temp_mean_C"] = 26.0
            weather_data[f"{city}_precip_mm"] = 0.0
            weather_data[f"{city}_wind_max_kmh"] = 15.0
            weather_data[f"{city}_gust_max_kmh"] = 20.0

    # Calculate averages across all 5 locations
    weather_data["avg_temp_mean_C"] = sum(weather_data[f"{c}_temp_mean_C"] for c in locations) / 5
    weather_data["avg_precip_mm"] = sum(weather_data[f"{c}_precip_mm"] for c in locations) / 5
    weather_data["avg_wind_max_kmh"] = sum(weather_data[f"{c}_wind_max_kmh"] for c in locations) / 5
    weather_data["avg_gust_max_kmh"] = sum(weather_data[f"{c}_gust_max_kmh"] for c in locations) / 5

    return weather_data
