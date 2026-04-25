#!/usr/bin/env python3
"""
Load backfilled Excel data into PostgreSQL database.
Also generates 3-day forecasts and stores them.
"""

import os
import sys
import pandas as pd
from datetime import date, timedelta
import traceback

# Set database URL
os.environ['DATABASE_URL'] = "postgresql://fishuser:DBPASSWORD@localhost:5432/fishprice"
os.environ['FISH'] = 'balaya'
os.environ['LOCATION'] = 'peliyagoda'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
import joblib

EXCEL_PATH = "historical_data.xlsx"
MODELS_DIR = "backend/models"
DATABASE_URL = os.environ.get("DATABASE_URL")

def load_excel_to_db():
    """Load Excel data into price_history table."""
    print("\n=== LOADING EXCEL DATA TO DATABASE ===\n")

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")

    engine = create_engine(DATABASE_URL)

    # Load Excel
    df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    print(f"Loaded {len(df)} rows from Excel")

    # Extract price history
    price_df = df[['date', 'price']].copy()
    price_df['location'] = 'peliyagoda'
    price_df['fish'] = 'balaya'
    price_df['source'] = 'excel_backfill'

    # Insert into database
    with engine.begin() as conn:
        # First, check what's already in the database
        existing = conn.execute(text("""
            SELECT COUNT(*) FROM price_history
            WHERE fish = 'balaya' AND location = 'peliyagoda'
        """)).fetchone()[0]

        print(f"Database currently has {existing} price records")

        # Clear existing or insert new
        for idx, row in price_df.iterrows():
            try:
                conn.execute(text("""
                    INSERT INTO price_history (date, price, location, fish, source)
                    VALUES (:date, :price, :location, :fish, :source)
                    ON CONFLICT (date, location, fish) DO UPDATE
                    SET price = EXCLUDED.price, source = EXCLUDED.source
                """), {
                    'date': row['date'],
                    'price': float(row['price']),
                    'location': row['location'],
                    'fish': row['fish'],
                    'source': row['source']
                })
            except Exception as e:
                print(f"Error inserting {row['date']}: {e}")

        # Verify
        new_count = conn.execute(text("""
            SELECT COUNT(*) FROM price_history
            WHERE fish = 'balaya' AND location = 'peliyagoda'
        """)).fetchone()[0]

        print(f"Database now has {new_count} price records")

        # Get latest date
        latest = conn.execute(text("""
            SELECT MAX(date) FROM price_history
            WHERE fish = 'balaya' AND location = 'peliyagoda'
        """)).fetchone()[0]

        print(f"Latest date in database: {latest.date() if latest else 'None'}")

def generate_and_store_forecasts():
    """Generate 3-day forecasts and store in database."""
    print("\n=== GENERATING & STORING FORECASTS ===\n")

    engine = create_engine(DATABASE_URL)
    df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # Compute features
    df['price_lag2'] = df['price'].shift(2).fillna(0)
    df['price_lag3'] = df['price'].shift(3).fillna(0)
    df['price_momentum_1'] = df['price'].diff(1).fillna(0)
    df['price_momentum_2'] = df['price'].diff(2).fillna(0)
    df['ema_3'] = df['price'].ewm(span=3, adjust=False).mean()
    df['rolling_std_3'] = df['price'].rolling(window=3, min_periods=1).std().fillna(0)
    df['rolling_max_3'] = df['price'].rolling(window=3, min_periods=1).max()
    df['rolling_min_3'] = df['price'].rolling(window=3, min_periods=1).min()
    df['price_range_3'] = df['rolling_max_3'] - df['rolling_min_3']

    latest_row = df.iloc[-1]

    feature_cols = [
        'year', 'month', 'day_of_week', 'is_weekend', 'day_of_year', 'is_poya',
        'is_national_holiday', 'is_market_holiday', 'Inflation_Rate',
        'Galle_production', 'Kalutara_production', 'Matara_production',
        'Negombo_production', 'Tangalla_production',
        'Matara_temp_mean_C', 'Matara_wind_max_kmh', 'Matara_gust_max_kmh', 'Matara_precip_mm',
        'Galle_temp_mean_C', 'Galle_wind_max_kmh', 'Galle_gust_max_kmh', 'Galle_precip_mm',
        'Negombo_temp_mean_C', 'Negombo_wind_max_kmh', 'Negombo_gust_max_kmh', 'Negombo_precip_mm',
        'Kalutara_temp_mean_C', 'Kalutara_precip_mm', 'Kalutara_wind_max_kmh', 'Kalutara_gust_max_kmh',
        'Tangalla_temp_mean_C', 'Tangalla_wind_max_kmh', 'Tangalla_gust_max_kmh', 'Tangalla_precip_mm',
        'LP 95', 'LP 92', 'LAD', 'LSD', 'LK',
        'quarter', 'day_of_month', 'week_of_year',
        'total_production', 'avg_temp_mean_C', 'avg_wind_max_kmh', 'avg_gust_max_kmh', 'avg_precip_mm',
        'price_change', 'price_lag1', 'price_lag2', 'price_lag3', 'price_lag7',
        'price_momentum_1', 'price_momentum_2', 'ema_3', 'rolling_std_3', 'rolling_max_3', 'rolling_min_3', 'price_range_3',
        'production_change', 'production_lag1', 'production_lag7'
    ]

    # Build feature vector
    import numpy as np
    X = np.zeros((1, len(feature_cols)))
    for i, col in enumerate(feature_cols):
        if col in df.columns:
            val = latest_row[col]
            X[0, i] = float(val) if pd.notna(val) else 0.0
        else:
            X[0, i] = 0.0

    # Calculate MA7
    ma7 = float(df['price'].tail(7).mean())
    print(f"MA7: {ma7:.2f}")

    # Generate forecasts
    forecast_date = date.today()
    forecasts = []

    with engine.begin() as conn:
        for h in range(1, 4):
            model_path = os.path.join(MODELS_DIR, f"balaya_h{h}.pkl")

            if not os.path.exists(model_path):
                print(f"WARNING: Model {model_path} not found, skipping horizon {h}")
                continue

            model = joblib.load(model_path)
            pred_xgb = float(model.predict(X)[0])
            blended = (0.5 * pred_xgb) + (0.5 * ma7)
            conf = blended * 0.05

            target_date = forecast_date + timedelta(days=h)

            print(f"H{h} ({target_date}): XGB={pred_xgb:.2f}, Blended={blended:.2f}")

            conn.execute(text("""
                INSERT INTO forecasts (forecast_date, horizon, blended_prediction, conf_lower, conf_upper, location, fish, model_version)
                VALUES (:forecast_date, :horizon, :pred, :lo, :hi, :location, :fish, :model_version)
                ON CONFLICT (forecast_date, horizon, location, fish) DO UPDATE
                SET blended_prediction = EXCLUDED.blended_prediction,
                    conf_lower = EXCLUDED.conf_lower,
                    conf_upper = EXCLUDED.conf_upper,
                    model_version = EXCLUDED.model_version,
                    generated_at = NOW()
            """), {
                'forecast_date': target_date,
                'horizon': h,
                'pred': blended,
                'lo': blended - conf,
                'hi': blended + conf,
                'location': 'peliyagoda',
                'fish': 'balaya',
                'model_version': 'xgboost_v1_blend'
            })

    print("Forecasts stored in database")

def main():
    print("=" * 60)
    print("LOAD DATA INTO DATABASE & GENERATE FORECASTS")
    print("=" * 60)

    try:
        # Load historical prices
        load_excel_to_db()

        # Generate and store forecasts
        generate_and_store_forecasts()

        print("\n" + "=" * 60)
        print("SUCCESS: Data loaded and forecasts generated")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
