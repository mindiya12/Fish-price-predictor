"""
Ensemble Inference Script - Phase 2
=====================================
Changes from Phase 1:
  - Loads both XGBoost (_h{n}.pkl) and LightGBM (_h{n}_lgbm.pkl) models
  - Predicts delta (price[t+h] - price[t]), then reconstructs absolute price
  - Applies 45% XGB + 45% LGBM + 10% rolling-baseline (row-wise)
  - Confidence bands from RMSE in model_metrics
  - Feature row built entirely from DB (no Excel dependency)
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from datetime import date, timedelta
from sqlalchemy import create_engine, text

# Add scripts dir to path for poya_days import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poya_days import POYA_DATES, days_until_next_poya, days_since_last_poya

DATABASE_URL = os.environ.get("DATABASE_URL")
FISH         = os.environ.get("FISH", "balaya")
LOCATION     = os.environ.get("LOCATION", "peliyagoda")
MODELS_DIR   = os.environ.get("MODELS_DIR", "/app/models")

# Phase 2 blend weights (must match train_models_xgb.py)
XGB_WEIGHT  = 0.45
LGBM_WEIGHT = 0.45
BASE_WEIGHT = 0.10


def build_inference_row(engine) -> pd.DataFrame:
    """
    Construct the feature row for inference entirely from the database,
    eliminating reliance on the Excel file and preventing feature drift.
    """
    with engine.connect() as conn:
        # --- Price history (last 35 rows for lag computation) ---
        price_rows = conn.execute(text("""
            SELECT date, price
            FROM price_history
            WHERE fish = :fish AND location = :location
            ORDER BY date DESC LIMIT 35
        """), {"fish": FISH, "location": LOCATION}).fetchall()

        if len(price_rows) < 8:
            raise RuntimeError(f"Insufficient price history: only {len(price_rows)} rows available (need 8+).")

        price_df = pd.DataFrame(price_rows, columns=["date", "price"])
        price_df["date"] = pd.to_datetime(price_df["date"])
        price_df = price_df.sort_values("date").reset_index(drop=True)

        latest = price_df.iloc[-1]
        d = latest["date"].date()
        price_today = float(latest["price"])

        # --- Latest weather (last available row for each city) ---
        weather_rows = conn.execute(text("""
            SELECT DISTINCT ON (city)
                city, temp_mean_c, wind_max_kmh, gust_max_kmh, precip_mm
            FROM weather_data
            ORDER BY city, date DESC
        """)).fetchall()

        # --- Fuel prices (latest available) ---
        fuel_row = conn.execute(text("""
            SELECT lp_95, lp_92, lad, lsd, lk
            FROM fuel_prices
            ORDER BY date DESC LIMIT 1
        """)).fetchone()

        # --- Inflation (latest available) ---
        inf_row = conn.execute(text("""
            SELECT ccpi_headline, ccpi_food
            FROM inflation_data
            ORDER BY reference_month DESC LIMIT 1
        """)).fetchone()

    # ── Build single-row feature dict ─────────────────────────────────────────
    row: dict = {}

    # Calendar
    row["year"]         = d.year
    row["month"]        = d.month
    row["day_of_week"]  = d.weekday()
    row["is_weekend"]   = int(d.weekday() >= 5)
    row["quarter"]      = (d.month - 1) // 3 + 1
    row["day_of_year"]  = d.timetuple().tm_yday
    row["day_of_month"] = d.day
    row["week_of_year"] = d.isocalendar()[1]

    # Cyclic
    row["sin_month"]    = np.sin(2 * np.pi * row["month"] / 12)
    row["cos_month"]    = np.cos(2 * np.pi * row["month"] / 12)
    row["sin_day_year"] = np.sin(2 * np.pi * row["day_of_year"] / 365)
    row["cos_day_year"] = np.cos(2 * np.pi * row["day_of_year"] / 365)
    row["sin_week"]     = np.sin(2 * np.pi * row["week_of_year"] / 52)
    row["cos_week"]     = np.cos(2 * np.pi * row["week_of_year"] / 52)

    # Holidays
    row["is_national_holiday"] = 0
    row["is_market_holiday"]   = row["is_weekend"]

    # Poya
    row["is_poya"]              = int(d in POYA_DATES)
    row["days_until_next_poya"] = days_until_next_poya(d)
    row["days_since_last_poya"] = days_since_last_poya(d)
    row["is_pre_poya"]          = int(row["days_until_next_poya"] in [1, 2])
    row["is_post_poya"]         = int(row["days_since_last_poya"] in [1, 2])

    # Macro
    row["Inflation_Rate"] = float(inf_row[0]) if inf_row and inf_row[0] else 0.0
    row["CCPI_Food"]      = float(inf_row[1]) if inf_row and inf_row[1] else 0.0

    # Fuel
    if fuel_row:
        row["LP 95"] = float(fuel_row[0] or 0)
        row["LP 92"] = float(fuel_row[1] or 0)
        row["LAD"]   = float(fuel_row[2] or 0)
        row["LSD"]   = float(fuel_row[3] or 0)
        row["LK"]    = float(fuel_row[4] or 0)
    else:
        for k in ["LP 95", "LP 92", "LAD", "LSD", "LK"]:
            row[k] = 0.0

    # Weather — pivot all available cities
    city_data: dict = {}
    for wr in weather_rows:
        city = wr[0]
        city_data[f"{city}_temp_mean_C"]  = float(wr[1] or 0)
        city_data[f"{city}_wind_max_kmh"] = float(wr[2] or 0)
        city_data[f"{city}_gust_max_kmh"] = float(wr[3] or 0)
        city_data[f"{city}_precip_mm"]    = float(wr[4] or 0)
    row.update(city_data)

    # Aggregate weather averages
    temp_cols = [v for k, v in city_data.items() if "_temp_mean_C" in k]
    row["avg_temp_mean_C"]  = np.mean([city_data[k] for k in city_data if "_temp_mean_C"  in k]) if city_data else 0.0
    row["avg_wind_max_kmh"] = np.mean([city_data[k] for k in city_data if "_wind_max_kmh" in k]) if city_data else 0.0
    row["avg_gust_max_kmh"] = np.mean([city_data[k] for k in city_data if "_gust_max_kmh" in k]) if city_data else 0.0
    row["avg_precip_mm"]    = np.mean([city_data[k] for k in city_data if "_precip_mm"    in k]) if city_data else 0.0

    # ── Price lag features from history ────────────────────────────────────
    # Cast to float64 — DB returns decimal.Decimal which breaks numpy arithmetic
    prices = price_df["price"].values.astype(float)  # ascending order

    for lag, offset in [(1, -1), (2, -2), (3, -3), (5, -5), (7, -7), (14, -14), (21, -21), (30, -30)]:
        idx = offset  # negative index from end
        row[f"price_lag{lag}"] = float(prices[idx]) if abs(offset) <= len(prices) else float(prices[0])

    # Rolling stats (on the shifted series = exclude current price)
    shifted = prices[:-1]  # everything except today
    for window in [3, 7, 14, 30]:
        window_data = shifted[-window:] if len(shifted) >= window else shifted
        row[f"price_roll_mean_{window}"] = float(np.mean(window_data))
        row[f"price_roll_std_{window}"]  = float(np.std(window_data)) if len(window_data) > 1 else 0.0
        row[f"price_roll_min_{window}"]  = float(np.min(window_data))
        row[f"price_roll_max_{window}"]  = float(np.max(window_data))
        row[f"price_roll_range_{window}"] = row[f"price_roll_max_{window}"] - row[f"price_roll_min_{window}"]

    # EWM: approximate at inference using available history
    price_series = pd.Series(shifted)
    row["price_ewm7"]  = float(price_series.ewm(span=7,  adjust=False).mean().iloc[-1])
    row["price_ewm14"] = float(price_series.ewm(span=14, adjust=False).mean().iloc[-1])
    row["price_ewm30"] = float(price_series.ewm(span=30, adjust=False).mean().iloc[-1])

    # Momentum
    row["price_change"]       = float(prices[-1] - prices[-2]) if len(prices) >= 2 else 0.0
    row["price_change_1d"]    = row["price_change"]
    row["price_change_7d"]    = float(prices[-1] - prices[-7])  if len(prices) >= 7  else 0.0
    row["price_change_14d"]   = float(prices[-1] - prices[-14]) if len(prices) >= 14 else 0.0
    row["price_pct_change_1d"] = row["price_change_1d"] / (prices[-2] + 1e-9) if len(prices) >= 2 else 0.0
    row["price_pct_change_7d"] = row["price_change_7d"] / (prices[-7] + 1e-9) if len(prices) >= 7 else 0.0

    prev_change = float(prices[-2] - prices[-3]) if len(prices) >= 3 else 0.0
    row["price_acceleration"]     = row["price_change_1d"] - prev_change
    row["price_dev_from_7d"]      = float(prices[-1]) - row["price_roll_mean_7"]
    row["price_dev_from_30d"]     = float(prices[-1]) - row["price_roll_mean_30"]
    row["price_trend_ratio_7_30"] = row["price_roll_mean_7"] / (row["price_roll_mean_30"] + 1e-9)

    # Volatility
    row["price_volatility_7d"]  = row["price_roll_std_7"]
    row["price_volatility_30d"] = row["price_roll_std_30"]

    # Production placeholders (no data yet)
    # (intentionally omitted — not used for training)

    # Keep today's observed price for reconstruction (not used as a model feature)
    row["price_current"] = price_today

    return pd.DataFrame([row])


def get_rmse_from_db(engine, horizon: int) -> float | None:
    """Fetch RMSE for a given horizon from the model_metrics table."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT rmse FROM model_metrics
                WHERE fish = :fish AND location = :location
                  AND horizon = :h AND is_production = TRUE
                ORDER BY trained_at DESC LIMIT 1
            """), {"fish": FISH, "location": LOCATION, "h": horizon}).fetchone()
        return float(result[0]) if result and result[0] else None
    except Exception:
        return None


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(DATABASE_URL)

    print("Building inference feature row from database...")
    X_latest = build_inference_row(engine)
    print(f"  Feature row shape: {X_latest.shape}")

    if "price_current" not in X_latest.columns:
        raise RuntimeError("Inference row missing price_current.")
    price_today = float(X_latest["price_current"].iloc[0])

    baseline_delta = 0.0
    if "price_roll_mean_7" in X_latest.columns:
        baseline_delta = float(X_latest["price_roll_mean_7"].iloc[0]) - price_today

    print(f"  Target: Δ(price) per horizon (price[t+h] - price[t])")
    print(f"  Blend: XGB×{XGB_WEIGHT}  LGBM×{LGBM_WEIGHT}  BASE×{BASE_WEIGHT}")

    forecast_date = date.today()
    predictions = {}

    for h in range(1, 4):
        xgb_path  = os.path.join(MODELS_DIR, f"{FISH}_h{h}.pkl")
        lgbm_path = os.path.join(MODELS_DIR, f"{FISH}_h{h}_lgbm.pkl")
        feat_path = os.path.join(MODELS_DIR, f"{FISH}_h{h}_features.pkl")

        if not os.path.exists(xgb_path):
            raise FileNotFoundError(f"XGB model not found: {xgb_path}")

        xgb_model = joblib.load(xgb_path)

        # Load the persisted feature list for alignment
        if os.path.exists(feat_path):
            feature_cols = joblib.load(feat_path)
            for mc in [c for c in feature_cols if c not in X_latest.columns]:
                X_latest[mc] = 0.0
            X_input = X_latest[feature_cols]
        elif hasattr(xgb_model, "feature_names_in_"):
            for mc in [c for c in xgb_model.feature_names_in_ if c not in X_latest.columns]:
                X_latest[mc] = 0.0
            X_input = X_latest[xgb_model.feature_names_in_]
        else:
            X_input = X_latest

        pred_xgb = float(xgb_model.predict(X_input)[0])

        # Phase 2: Try loading LightGBM model
        if os.path.exists(lgbm_path):
            lgbm_model = joblib.load(lgbm_path)
            pred_lgbm  = float(lgbm_model.predict(X_input)[0])
            blended_delta = XGB_WEIGHT * pred_xgb + LGBM_WEIGHT * pred_lgbm + BASE_WEIGHT * baseline_delta
        else:
            # Fallback: delta-only if LGBM not yet trained
            pred_lgbm = pred_xgb
            blended_delta = pred_xgb

        blended = price_today + blended_delta

        rmse = get_rmse_from_db(engine, h)
        lo = blended - rmse if rmse else blended * 0.95
        hi = blended + rmse if rmse else blended * 1.05

        predictions[h] = {
            "xgb": pred_xgb, "lgbm": pred_lgbm,
            "blended": blended, "lo": lo, "hi": hi,
            "rmse": rmse or 0.0,
        }

    print("\nInference results:")
    for h, p in predictions.items():
        target = forecast_date + timedelta(days=h)
        print(f"  h={h} ({target}): ΔXGB={p['xgb']:+.1f}  ΔLGBM={p['lgbm']:+.1f}  Price={p['blended']:.1f}  CI=[{p['lo']:.0f},{p['hi']:.0f}]  RMSE±{p['rmse']:.1f}")

    # Upsert into forecasts table
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
                "horizon":       h,
                "pred":          predictions[h]["blended"],
                "lo":            predictions[h]["lo"],
                "hi":            predictions[h]["hi"],
                "location":      LOCATION,
                "fish":          FISH,
                "model_version": "ensemble_p2_delta",
            })

    print("\n✅ Phase 2 ensemble forecasts saved to database successfully.")


if __name__ == "__main__":
    main()
