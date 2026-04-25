from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import subprocess
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import text
import traceback
import sys

from app.db.session import engine
from app.services.scraper import download_cbsl_report, extract_balaya_peliyagoda_today, fetch_open_meteo_weather

router = APIRouter()

EXCEL_PATH = "/data/historical_data.xlsx"

class ScrapeResponse(BaseModel):
    status: str
    message: str
    date: str
    price: float | None
    weather_fetched: bool

def run_inference():
    """Runs the data scraping pipelines and new ML training/inference script."""
    try:
        base_cmd = [sys.executable, "-m"]
        print("Triggering weather, fuel, and inflation scrapers...")
        subprocess.run(base_cmd + ["scripts.scrape_weather"], check=True)
        subprocess.run(base_cmd + ["scripts.scrape_fuel_prices"], check=True)
        subprocess.run(base_cmd + ["scripts.scrape_inflation"], check=True)

        print("Triggering XGBoost Training & Inference...")
        subprocess.run([sys.executable, "scripts/train_models_xgb.py"], check=True)
    except Exception as e:
        print(f"Scrape/Inference pipeline failed: {e}")

def run_daily_scrape(target_date: str | None = None):
    """Core logic to scrape and store fish prices."""
    try:
        if target_date:
            d = date.fromisoformat(target_date)
        else:
            d = date.today()
            
        print(f"Running daily scrape for: {d}")
        final_price = 0.0
        weather_fetched = False

        # 1. Scrape Price
        pdf_path = download_cbsl_report(d)
        price_today = None
        if pdf_path:
            price_today = extract_balaya_peliyagoda_today(pdf_path)

        # 2. Get Weather
        weather_data = fetch_open_meteo_weather(d)
        weather_fetched = bool(weather_data)

        # 3. Check if data already exists in DB or Excel
        with engine.connect() as conn:
            db_check = conn.execute(text("""
                SELECT 1 FROM price_history 
                WHERE date = :date AND location = 'peliyagoda' AND fish = 'balaya'
            """), {"date": d}).fetchone()

        df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
        df["date"] = pd.to_datetime(df["date"])
        last_row = df.sort_values("date").iloc[-1]
        excel_check = not df[df["date"] == pd.Timestamp(d)].empty

        if db_check and excel_check:
            print(f"Data for {d} already exists in both DB and Excel.")
            return {
                "status": "skipped",
                "message": f"Data for {d} already exists.",
                "date": str(d),
                "price": None,
                "weather_fetched": False
            }

        # If price is missing (e.g., weekend), forward-fill price
        final_price = float(price_today) if price_today is not None else float(last_row["price"])
        print(f"DEBUG: final_price={final_price}")

        # 4. Compute Features
        new_row = {}
        new_row["date"] = pd.Timestamp(d)
        new_row["price"] = final_price
        new_row["year"] = d.year
        new_row["month"] = d.month
        new_row["day_of_week"] = d.weekday()
        new_row["is_weekend"] = 1 if d.weekday() >= 5 else 0
        new_row["quarter"] = (d.month - 1) // 3 + 1
        new_row["day_of_year"] = d.timetuple().tm_yday
        new_row["day_of_month"] = d.day
        new_row["week_of_year"] = d.isocalendar()[1]
        new_row["is_poya"] = 0 
        new_row["is_national_holiday"] = 0
        new_row["is_market_holiday"] = 1 if new_row["is_weekend"] else 0

        for k, v in weather_data.items():
            new_row[k] = v

        new_row["price_lag1"] = last_row["price"]
        if len(df) >= 7:
            new_row["price_lag7"] = df.iloc[-7]["price"]
        else:
            new_row["price_lag7"] = last_row["price"]
        new_row["price_change"] = new_row["price"] - new_row["price_lag1"]

        macro_features = [
            'Inflation_Rate', 'Galle_production', 'Kalutara_production', 
            'Matara_production', 'Negombo_production', 'Tangalla_production', 
            'LP 95', 'LP 92', 'LAD', 'LSD', 'LK', 'total_production',
            'production_change', 'production_lag1', 'production_lag7'
        ]
        for mf in macro_features:
            if mf in last_row:
                new_row[mf] = last_row[mf]
            else:
                new_row[mf] = 0.0
                
        # 5. Save to Excel if missing
        if not excel_check:
            df = df.sort_values("date").reset_index(drop=True)
            last_row = df.iloc[-1]
            new_df = pd.DataFrame([new_row])
            for col in df.columns:
                if col not in new_df.columns:
                    new_df[col] = last_row[col]
            new_df = new_df[df.columns]
            updated_df = pd.concat([df, new_df], ignore_index=True)
            updated_df.to_excel(EXCEL_PATH, index=False, engine="openpyxl")
            print(f"Appended {d} to {EXCEL_PATH}")
        else:
            print(f"Skipped Excel append for {d} (already exists).")

        # 6. Save to PostgreSQL if missing
        if not db_check:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO price_history (date, price, location, fish, source)
                    VALUES (:date, :price, 'peliyagoda', 'balaya', 'scheduler')
                    ON CONFLICT (date, location, fish) DO UPDATE
                    SET price = EXCLUDED.price, source = EXCLUDED.source
                """), {"date": d, "price": final_price})
            print("Inserted into price_history table.")
            
            # 6.1 Sync Forecast with actual price for Accuracy Tracking
            try:
                with engine.begin() as conn:
                    # Find if we have a forecast for this date
                    forecast_row = conn.execute(text("""
                        SELECT blended_prediction, horizon, model_version
                        FROM forecasts
                        WHERE forecast_date = :date AND fish = 'balaya' AND location = 'peliyagoda'
                        ORDER BY generated_at DESC LIMIT 1
                    """), {"date": d}).fetchone()
                    
                    if forecast_row:
                        pred_price, horizon, version = forecast_row
                        conn.execute(text("""
                            INSERT INTO predictions (forecast_date, horizon, predicted_price, actual_price, fish, location, model_version)
                            VALUES (:date, :horizon, :pred, :actual, 'balaya', 'peliyagoda', :version)
                            ON CONFLICT (forecast_date, horizon, fish, location) DO UPDATE
                            SET actual_price = EXCLUDED.actual_price, predicted_price = EXCLUDED.predicted_price
                        """), {
                            "date": d, 
                            "horizon": horizon, 
                            "pred": pred_price, 
                            "actual": final_price, 
                            "version": version
                        })
                        print(f"Synced prediction for {d} (Pred: {pred_price}, Actual: {final_price})")
            except Exception as e:
                print(f"Failed to sync prediction: {e}")
        else:
            print(f"Skipped DB insert for {d} (already exists).")

        # 7. Trigger Inference
        run_inference()

        return {
            "status": "success",
            "message": "Data scraped and inference completed.",
            "date": str(d),
            "price": final_price,
            "weather_fetched": weather_fetched
        }

    except Exception as e:
        traceback.print_exc()
        raise e

@router.post("/api/admin/scrape-daily", response_model=ScrapeResponse)
def scrape_daily(target_date: str | None = None, background_tasks: BackgroundTasks = BackgroundTasks()):
    """Triggered via API (e.g., manual or n8n)."""
    try:
        result = run_daily_scrape(target_date)
        return ScrapeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
