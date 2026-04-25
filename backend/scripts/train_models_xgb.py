"""
XGBoost Training Script - DB-Driven Pipeline
=============================================
Trains 7 horizon-specific XGBoost models using data collected from
the scraping pipelines (price_history, weather_data, fuel_prices, inflation_data).

This replaces the Excel-based training and uses the exact same model
architecture as the original training code (1500 estimators, depth=6, lr=0.02).

Pipeline:
  1. Build a training_df by joining all tables in the DB by date
  2. Compute lag features (price_lag1, price_lag7, price_change) from price_history
  3. Forward-fill inflation/fuel prices (monthly/periodic data)
  4. Apply identical cleaning & feature col selection as original training
  5. Train 7 XGBRegressor models (one per forecast horizon)
  6. Evaluate on last 30 days of data
  7. Save updated .pkl model files
  8. Write metrics to model_metrics table
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
import warnings
from datetime import date
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

DATABASE_URL = os.environ.get("DATABASE_URL")
FISH         = os.environ.get("FISH", "balaya")
LOCATION     = os.environ.get("LOCATION", "peliyagoda")
MODELS_DIR   = os.environ.get("MODELS_DIR", "/app/models")

BEST_PARAMS = {
    "n_estimators":    1500,
    "max_depth":       6,
    "learning_rate":   0.02,
    "subsample":       0.8,
    "colsample_bytree":0.8,
    "random_state":    42,
    "n_jobs":          -1,
}

TARGET_COL = "price"
COLS_TO_EXCLUDE = ["date", "season", TARGET_COL]


def load_training_data(engine) -> pd.DataFrame:
    """
    Build a daily training DataFrame by joining:
      - price_history  (daily price)
      - weather_data   (daily per city, pivoted wide)
      - fuel_prices    (periodic, forward-filled)
      - inflation_data (monthly, forward-filled)
    """
    # 1. Load price history
    print("Loading price history...")
    price_df = pd.read_sql(text("""
        SELECT date, price
        FROM price_history
        WHERE fish = :fish AND location = :location
        ORDER BY date ASC
    """), engine, params={"fish": FISH, "location": LOCATION})
    price_df["date"] = pd.to_datetime(price_df["date"])

    # 2. Load and pivot weather data
    print("Loading weather data...")
    weather_df = pd.read_sql(text("""
        SELECT date, city, temp_mean_c, wind_max_kmh, gust_max_kmh, precip_mm
        FROM weather_data
        ORDER BY date, city
    """), engine)
    weather_df["date"] = pd.to_datetime(weather_df["date"])

    # Pivot: one row per date with columns like Galle_temp_mean_C, etc.
    weather_pivot = weather_df.pivot_table(
        index="date", columns="city",
        values=["temp_mean_c", "wind_max_kmh", "gust_max_kmh", "precip_mm"],
        aggfunc="mean"
    )
    # Flatten column names: (temp_mean_c, Galle) → Galle_temp_mean_C
    metric_map = {
        "temp_mean_c":  "temp_mean_C",
        "wind_max_kmh": "wind_max_kmh",
        "gust_max_kmh": "gust_max_kmh",
        "precip_mm":    "precip_mm",
    }
    weather_pivot.columns = [
        f"{city}_{metric_map.get(metric, metric)}"
        for metric, city in weather_pivot.columns
    ]
    weather_pivot = weather_pivot.reset_index()

    # Add aggregate averages
    cities = weather_df["city"].unique().tolist()
    weather_pivot["avg_temp_mean_C"]  = weather_pivot[[f"{c}_temp_mean_C"  for c in cities if f"{c}_temp_mean_C"  in weather_pivot.columns]].mean(axis=1)
    weather_pivot["avg_wind_max_kmh"] = weather_pivot[[f"{c}_wind_max_kmh" for c in cities if f"{c}_wind_max_kmh" in weather_pivot.columns]].mean(axis=1)
    weather_pivot["avg_gust_max_kmh"] = weather_pivot[[f"{c}_gust_max_kmh" for c in cities if f"{c}_gust_max_kmh" in weather_pivot.columns]].mean(axis=1)
    weather_pivot["avg_precip_mm"]    = weather_pivot[[f"{c}_precip_mm"    for c in cities if f"{c}_precip_mm"    in weather_pivot.columns]].mean(axis=1)

    # 3. Load fuel prices
    print("Loading fuel prices...")
    fuel_df = pd.read_sql(text("SELECT date, lp_95, lp_92, lad, lsd, lk FROM fuel_prices ORDER BY date"), engine)
    fuel_df["date"] = pd.to_datetime(fuel_df["date"])
    fuel_df.rename(columns={"lp_95": "LP 95", "lp_92": "LP 92", "lad": "LAD", "lsd": "LSD", "lk": "LK"}, inplace=True)

    # 4. Load inflation data
    print("Loading inflation data...")
    inf_df = pd.read_sql(text("SELECT reference_month, ccpi_headline FROM inflation_data ORDER BY reference_month"), engine)
    inf_df["date"] = pd.to_datetime(inf_df["reference_month"])
    inf_df.rename(columns={"ccpi_headline": "Inflation_Rate"}, inplace=True)
    inf_df = inf_df[["date", "Inflation_Rate"]]

    # 5. Merge all on date
    df = price_df.merge(weather_pivot, on="date", how="left")
    df = df.merge(fuel_df, on="date", how="left")
    # For inflation, merge on year-month and forward-fill
    df["ym"] = df["date"].dt.to_period("M").dt.to_timestamp()
    inf_df["ym"] = inf_df["date"].dt.to_period("M").dt.to_timestamp()
    df = df.merge(inf_df[["ym", "Inflation_Rate"]], on="ym", how="left").drop("ym", axis=1)

    # Forward-fill fuel + inflation (they don't change daily)
    for col in ["LP 95", "LP 92", "LAD", "LSD", "LK", "Inflation_Rate"]:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()

    # 6. Compute calendar features
    df["year"]         = df["date"].dt.year
    df["month"]        = df["date"].dt.month
    df["day_of_week"]  = df["date"].dt.dayofweek
    df["is_weekend"]   = (df["day_of_week"] >= 5).astype(int)
    df["quarter"]      = df["date"].dt.quarter
    df["day_of_year"]  = df["date"].dt.dayofyear
    df["day_of_month"] = df["date"].dt.day
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)

    # Placeholder features (require external data sources)
    df["is_poya"]             = 0
    df["is_national_holiday"] = 0
    df["is_market_holiday"]   = df["is_weekend"]

    # 7. Compute price lag features
    df["price_lag1"]  = df["price"].shift(1)
    df["price_lag7"]  = df["price"].shift(7)
    df["price_change"] = df["price"] - df["price_lag1"]

    # 8. Drop rows without lag data
    df = df.dropna(subset=["price_lag1", "price_lag7"]).reset_index(drop=True)

    print(f"Training data: {len(df)} rows from {df['date'].min().date()} to {df['date'].max().date()}")
    return df


def clean_data(df, feats):
    """Fill NaN with column median for all feature columns."""
    for col in feats:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())
    return df


def get_feature_cols(df):
    """Return feature columns that exist in the data (excluding target/metadata)."""
    core_features = [
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
    # Use only columns that actually exist
    available = [c for c in core_features if c in df.columns]
    # Also include any additional columns not in exclude list
    extra = [c for c in df.columns if c not in COLS_TO_EXCLUDE + ["date", "ym"] and c not in available]
    return available + extra


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(DATABASE_URL)

    # Load and prepare data
    df = load_training_data(engine)
    feature_cols = get_feature_cols(df)
    print(f"Using {len(feature_cols)} features: {feature_cols[:8]}...")

    # Train/test split: last 30 days = test, rest = train
    test_size = 30
    train_df = df.iloc[:-test_size].copy()
    test_df  = df.iloc[-test_size:].copy()

    train_df = clean_data(train_df, feature_cols)
    test_df  = clean_data(test_df,  feature_cols)

    print(f"\nTrain: {len(train_df)} rows | Test: {len(test_df)} rows")
    print("\nTraining 3 horizon-specific models...")

    os.makedirs(MODELS_DIR, exist_ok=True)
    models = {}
    metrics = []

    for h in range(1, 4):
        print(f"\n--- Horizon h={h} ---")

        y_train = train_df[TARGET_COL].shift(-h).dropna()
        X_train = train_df[feature_cols].iloc[:len(y_train)]

        y_test  = test_df[TARGET_COL].shift(-h).dropna()
        X_test  = test_df[feature_cols].iloc[:len(y_test)]

        model = XGBRegressor(**BEST_PARAMS)
        model.fit(X_train, y_train)

        if len(y_test) > 0:
            preds = model.predict(X_test)
            rmse  = float(np.sqrt(mean_squared_error(y_test, preds)))
            mae   = float(mean_absolute_error(y_test, preds))
            mape  = float(mean_absolute_percentage_error(y_test, preds) * 100)
            print(f"  RMSE: {rmse:.2f}  MAE: {mae:.2f}  MAPE: {mape:.2f}%")
        else:
            rmse, mae, mape = 0.0, 0.0, 0.0

        model_path = os.path.join(MODELS_DIR, f"{FISH}_h{h}.pkl")
        joblib.dump(model, model_path)
        print(f"  Saved: {model_path}")

        models[h] = model
        metrics.append({"horizon": h, "rmse": rmse, "mae": mae, "mape": mape})

    # Save metrics to DB
    model_version = f"xgboost_{pd.Timestamp.now().strftime('%Y%m%d')}"
    insert_q = text("""
        INSERT INTO model_metrics (model_version, horizon, rmse, mae, mape, fish, location, is_production)
        VALUES (:version, :horizon, :rmse, :mae, :mape, :fish, :location, TRUE)
        ON CONFLICT (model_version, horizon, fish, location) DO UPDATE
        SET rmse=EXCLUDED.rmse, mae=EXCLUDED.mae, mape=EXCLUDED.mape, trained_at=NOW()
    """)

    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE model_metrics SET is_production=FALSE WHERE fish=:fish AND location=:location"
        ), {"fish": FISH, "location": LOCATION})
        for m in metrics:
            conn.execute(insert_q, {
                "version":  model_version,
                "horizon":  m["horizon"],
                "rmse":     m["rmse"],
                "mae":      m["mae"],
                "mape":     m["mape"],
                "fish":     FISH,
                "location": LOCATION,
            })

    print(f"\n✅ Retraining complete. Models saved. Version: {model_version}")

    # Generate and save final blended forecast
    last_row = test_df.iloc[[-1]]
    ma7 = df["price"].tail(7).mean()
    generation_date = df["date"].iloc[-1].date()

    print(f"\n3-day forecast (MA7={ma7:.0f}) generated on {generation_date}:")

    forecast_insert_q = text("""
        INSERT INTO forecasts (forecast_date, horizon, blended_prediction, model_version, fish, location)
        VALUES (:f_date, :horizon, :price, :version, :fish, :location)
        ON CONFLICT (forecast_date, horizon, fish, location) DO UPDATE
        SET blended_prediction = EXCLUDED.blended_prediction, model_version = EXCLUDED.model_version, generated_at = NOW()
    """)

    with engine.begin() as conn:
        for h in range(1, 4):
            xgb_pred   = float(models[h].predict(last_row[feature_cols])[0])
            blended    = float(0.5 * xgb_pred + 0.5 * float(ma7))
            target_day = (df["date"].iloc[-1] + pd.Timedelta(days=h)).date()
            
            print(f"  {target_day}: {blended:.2f}")
            
            conn.execute(forecast_insert_q, {
                "f_date":   target_day,
                "horizon":  h,
                "price":    blended,
                "version":  model_version,
                "fish":     FISH,
                "location": LOCATION,
            })

            
    print("\n✅ Forecast saved to database successfully.")

if __name__ == "__main__":
    main()
