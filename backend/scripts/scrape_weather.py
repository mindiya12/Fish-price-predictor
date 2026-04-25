"""
Weather Data Scraper - Open-Meteo API
======================================
Fetches daily weather data for 5 coastal fishing locations in Sri Lanka
and stores it in the `weather_data` table.

Locations and coordinates:
  Galle     (6.0535, 80.2210)
  Matara    (5.9485, 80.5353)
  Negombo   (7.2008, 79.8737)
  Kalutara  (6.5854, 79.9607)
  Tangalla  (6.0240, 80.7941)

Features produced (per city):
  {City}_temp_mean_C     -> temperature_2m_mean
  {City}_wind_max_kmh    -> windspeed_10m_max
  {City}_gust_max_kmh    -> windgusts_10m_max
  {City}_precip_mm       -> precipitation_sum

Computed aggregates:
  avg_temp_mean_C, avg_wind_max_kmh, avg_gust_max_kmh, avg_precip_mm
"""

import os
import requests
from datetime import date, timedelta, datetime
from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = os.environ.get("DATABASE_URL")

LOCATIONS = {
    "Galle":    {"lat": 6.0535,  "lon": 80.2210},
    "Matara":   {"lat": 5.9485,  "lon": 80.5353},
    "Negombo":  {"lat": 7.2008,  "lon": 79.8737},
    "Kalutara": {"lat": 6.5854,  "lon": 79.9607},
    "Tangalla": {"lat": 6.0240,  "lon": 80.7941},
}

# Open-Meteo archive API works for past data.
# Forecast API handles near-future & recent days.
ARCHIVE_URL  = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_PARAMS = "windspeed_10m_max,windgusts_10m_max,precipitation_sum,temperature_2m_mean"
TIMEZONE     = "Asia/Colombo"
BACKFILL_START = date(2017, 1, 1)


def _create_table(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id                   SERIAL PRIMARY KEY,
            date                 DATE NOT NULL,
            city                 TEXT NOT NULL,
            temp_mean_c          NUMERIC,
            wind_max_kmh         NUMERIC,
            gust_max_kmh         NUMERIC,
            precip_mm            NUMERIC,
            created_at           TIMESTAMP DEFAULT NOW(),
            UNIQUE (date, city)
        );
        CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date);
    """))


def _fetch_weather(city: str, lat: float, lon: float,
                   start: date, end: date) -> pd.DataFrame:
    """Fetch weather from Open-Meteo for a single location and date range."""
    
    def _fetch_chunk(url, c_start, c_end):
        params = {
            "latitude":  lat,
            "longitude": lon,
            "start_date": c_start.isoformat(),
            "end_date":   c_end.isoformat(),
            "daily":      DAILY_PARAMS,
            "timezone":   TIMEZONE,
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json().get("daily", {})
        
        times = data.get("time", [])
        dates = pd.to_datetime(times).date.tolist()
        return pd.DataFrame({
            "date":         dates,
            "city":         city,
            "temp_mean_c":  data.get("temperature_2m_mean", [None] * len(dates)),
            "wind_max_kmh": data.get("windspeed_10m_max",   [None] * len(dates)),
            "gust_max_kmh": data.get("windgusts_10m_max",   [None] * len(dates)),
            "precip_mm":    data.get("precipitation_sum",   [None] * len(dates)),
        })

    dfs = []
    archive_end = date.today() - timedelta(days=5)
    
    try:
        if start <= archive_end:
            chunk_end = min(end, archive_end)
            dfs.append(_fetch_chunk(ARCHIVE_URL, start, chunk_end))
        
        if end > archive_end:
            chunk_start = max(start, archive_end + timedelta(days=1))
            dfs.append(_fetch_chunk(FORECAST_URL, chunk_start, end))
            
        if not dfs:
            return pd.DataFrame()
            
        return pd.concat(dfs, ignore_index=True)
        
    except Exception as e:
        print(f"Error fetching weather for {city}: {e}")
        return pd.DataFrame()


def _get_latest_date_in_db(engine, city: str) -> date | None:
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT MAX(date) FROM weather_data WHERE city = :city"
        ), {"city": city}).fetchone()
    return row[0] if row and row[0] else None


def backfill_weather(engine, start: date = None, end: date = None):
    """
    Backfill weather data for all cities.
    On first run, fetches from BACKFILL_START to today.
    On subsequent runs, only fetches missing dates.
    """
    with engine.begin() as conn:
        _create_table(conn)

    if end is None:
        end = date.today()

    total = 0
    for city, coords in LOCATIONS.items():
        city_start = start
        if city_start is None:
            latest = _get_latest_date_in_db(engine, city)
            city_start = (latest + timedelta(days=1)) if latest else BACKFILL_START

        if city_start > end:
            print(f"{city}: Already up to date.")
            continue

        print(f"Fetching {city}: {city_start} → {end}")
        df = _fetch_weather(city, coords["lat"], coords["lon"], city_start, end)

        if df.empty:
            print(f"  No data returned for {city}.")
            continue

        with engine.begin() as conn:
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO weather_data (date, city, temp_mean_c, wind_max_kmh, gust_max_kmh, precip_mm)
                    VALUES (:date, :city, :temp, :wind, :gust, :precip)
                    ON CONFLICT (date, city) DO UPDATE
                        SET temp_mean_c   = EXCLUDED.temp_mean_c,
                            wind_max_kmh  = EXCLUDED.wind_max_kmh,
                            gust_max_kmh  = EXCLUDED.gust_max_kmh,
                            precip_mm     = EXCLUDED.precip_mm
                """), {
                    "date":  row["date"],
                    "city":  row["city"],
                    "temp":  row["temp_mean_c"] if pd.notna(row["temp_mean_c"]) else 26.0,
                    "wind":  row["wind_max_kmh"] if pd.notna(row["wind_max_kmh"]) else 15.0,
                    "gust":  row["gust_max_kmh"] if pd.notna(row["gust_max_kmh"]) else 20.0,
                    "precip":row["precip_mm"] if pd.notna(row["precip_mm"]) else 0.0,
                })
        
        count = len(df)
        print(f"  Saved {count} records for {city}.")
        total += count

    return total


def get_weather_for_date(engine, target_date: date) -> dict:
    """
    Returns a flat dict of weather features for the given date,
    matching the model's expected column names.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT city, temp_mean_c, wind_max_kmh, gust_max_kmh, precip_mm
            FROM weather_data
            WHERE date = :date
        """), {"date": target_date}).fetchall()

    if not rows:
        return {}

    result = {}
    temps, winds, gusts, precips = [], [], [], []
    for city, temp, wind, gust, precip in rows:
        result[f"{city}_temp_mean_C"]  = float(temp  or 26.0)
        result[f"{city}_wind_max_kmh"] = float(wind  or 15.0)
        result[f"{city}_gust_max_kmh"] = float(gust  or 20.0)
        result[f"{city}_precip_mm"]    = float(precip or 0.0)
        temps.append(result[f"{city}_temp_mean_C"])
        winds.append(result[f"{city}_wind_max_kmh"])
        gusts.append(result[f"{city}_gust_max_kmh"])
        precips.append(result[f"{city}_precip_mm"])

    # Aggregate averages used as model features
    if temps:
        result["avg_temp_mean_C"]  = sum(temps)  / len(temps)
        result["avg_wind_max_kmh"] = sum(winds)  / len(winds)
        result["avg_gust_max_kmh"] = sum(gusts)  / len(gusts)
        result["avg_precip_mm"]    = sum(precips) / len(precips)

    return result


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(DATABASE_URL)
    print("Starting weather data backfill...")
    count = backfill_weather(engine)
    print(f"Weather backfill complete. Total records saved: {count}")


if __name__ == "__main__":
    main()
