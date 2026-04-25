import os
import joblib
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
FISH = os.environ.get("FISH", "balaya")
LOCATION = os.environ.get("LOCATION", "peliyagoda")
EXCEL_PATH = "/data/historical_data.xlsx"
MODELS_DIR = os.environ.get("MODELS_DIR", "/app/models")

def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(DATABASE_URL)

    print("Loading latest data from Excel for feature extraction...")
    # Load just enough data to get the latest row safely
    df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    
    # Sort to ensure latest is at the end, drop fully empty rows
    df = df.dropna(how='all').sort_values('date').reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    print(f"Sanitized columns: {df.columns.tolist()[:3]}...")
    print(f"Loaded DF columns: {df.columns.tolist()[:5]}... (total {len(df.columns)})")
    
    # The models expect 53 specific features. We get them from the very last row in the Excel file
    latest_row = df.iloc[-1:]
    latest_date_in_excel = latest_row['date'].iloc[0]
    print(f"Latest row columns: {latest_row.columns.tolist()[:5]}... (total {len(latest_row.columns)})")
    print(f"Latest data in Excel is from: {latest_date_in_excel}")
    
    # The models expect 53 specific features. We get them from the very last row in the Excel file
    feature_cols = [
        'year', 'month', 'day_of_week', 'is_weekend', 'day_of_year', 'is_poya', 
        'is_national_holiday', 'is_market_holiday', 'Inflation_Rate', 'Galle_production', 
        'Kalutara_production', 'Matara_production', 'Negombo_production', 'Tangalla_production', 
        'Matara_temp_mean_C', 'Matara_wind_max_kmh', 'Matara_gust_max_kmh', 'Matara_precip_mm', 
        'Galle_temp_mean_C', 'Galle_wind_max_kmh', 'Galle_gust_max_kmh', 'Galle_precip_mm', 
        'Negombo_temp_mean_C', 'Negombo_wind_max_kmh', 'Negombo_gust_max_kmh', 'Negombo_precip_mm', 
        'Kalutara_temp_mean_C', 'Kalutara_precip_mm', 'Kalutara_wind_max_kmh', 'Kalutara_gust_max_kmh', 
        'Tangalla_temp_mean_C', 'Tangalla_wind_max_kmh', 'Tangalla_gust_max_kmh', 'Tangalla_precip_mm', 
        'LP 95', 'LP 92', 'LAD', 'LSD', 'LK', 'quarter', 'day_of_month', 'week_of_year', 
        'total_production', 'avg_temp_mean_C', 'avg_wind_max_kmh', 'avg_gust_max_kmh', 'avg_precip_mm', 
        'price_change', 'price_lag1', 'price_lag7', 'production_change', 'production_lag1', 'production_lag7'
    ]
    
    # Intersection check
    existing_cols = list(df.columns)
    print(f"DEBUG: df.columns type: {type(df.columns)}")
    print(f"DEBUG: Example column repr: {repr(existing_cols[0])}")
    
    missing = [c for c in feature_cols if c not in existing_cols]
    if missing:
        print(f"ERROR: Missing features in Excel: {missing}")
        raise KeyError(f"Missing columns: {missing}")
    
    # Selecting features one by one if necessary
    try:
        X_latest = latest_row[feature_cols].copy()
    except Exception as e:
        print(f"DEBUG: Initial selection failed: {e}")
        # Manual selection
        data_dict = {}
        for c in feature_cols:
            data_dict[c] = latest_row[c].values
        X_latest = pd.DataFrame(data_dict)
    
    print(f"X_latest shape: {X_latest.shape}")
    print(f"X_latest columns: {X_latest.columns.tolist()[:5]}")

    # Calculate MA7 for blending
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT price FROM price_history
            WHERE fish = :fish AND location = :location
            ORDER BY date DESC LIMIT 7
        """), {"fish": FISH, "location": LOCATION}).fetchall()
        
        if len(rows) < 7:
            print("Warning: Less than 7 days of price history available. MA7 will be purely based on available data.")
            ma7 = float(df.iloc[-1]['price']) # fallback to last known price
        else:
            ma7 = sum([float(r[0]) for r in rows]) / 7.0

    print(f"Calculated MA7 for blending: {ma7:.2f}")

    # For safety, base the forecast date on the current UTC date, 
    # but since this might run for historical tests, we align it with what's in the DB.
    # We will use today's date as the "forecast_date" to represent when it was generated.
    forecast_date = date.today()

    # We will loop through horizons 1 to 3
    predictions = {}
    for h in range(1, 4):
        model_path = os.path.join(MODELS_DIR, f"{FISH}_h{h}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
            
        print(f"Loading model for horizon {h}: {model_path}")
        model = joblib.load(model_path)
        
        # Inference
        # Ensure feature alignment if the model has feature_names_ in for scikit-learn
        if hasattr(model, 'feature_names_in_'):
            X_latest = X_latest[model.feature_names_in_]
        
        pred_xgb = float(model.predict(X_latest)[0])
        
        # Blend: 50% XGBoost, 50% MA7 (per roadmap)
        blended = (0.5 * pred_xgb) + (0.5 * ma7)
        
        # Confidence bands (placeholder 5% margin until model_metrics table has RMSE)
        conf = blended * 0.05
        lo = blended - conf
        hi = blended + conf
        
        predictions[h] = {
            "xgb": pred_xgb,
            "blended": blended,
            "lo": lo,
            "hi": hi
        }
        
    print("Inference complete. Upserting into database...")

    # Upsert into PostgreSQL
    insert_q = text("""
        INSERT INTO forecasts (forecast_date, horizon, blended_prediction, conf_lower, conf_upper, location, fish, model_version)
        VALUES (:forecast_date, :horizon, :pred, :lo, :hi, :location, :fish, :model_version)
        ON CONFLICT (forecast_date, horizon, location, fish) DO UPDATE
        SET blended_prediction = EXCLUDED.blended_prediction,
            conf_lower = EXCLUDED.conf_lower,
            conf_upper = EXCLUDED.conf_upper,
            model_version = EXCLUDED.model_version,
            generated_at = NOW()
    """)

    with engine.begin() as conn:
        for h in range(1, 4):
            target_date = forecast_date + timedelta(days=h)
            conn.execute(insert_q, {
                "forecast_date": target_date,
                "horizon": h,
                "pred": predictions[h]["blended"],
                "lo": predictions[h]["lo"],
                "hi": predictions[h]["hi"],
                "location": LOCATION,
                "fish": FISH,
                "model_version": "xgboost_v1_blend",
            })
            print(f"Horizon {h} ({target_date}): XGB={predictions[h]['xgb']:.2f}, Blended={predictions[h]['blended']:.2f}")

    print("Successfully generated and saved XGBoost forecasts.")

if __name__ == "__main__":
    main()
