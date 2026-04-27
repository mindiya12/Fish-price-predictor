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

        # --- Weather history (for lagged aggregates) ---
        weather_hist = conn.execute(text("""
            SELECT date, city, temp_mean_c, wind_max_kmh, gust_max_kmh, precip_mm
            FROM weather_data
            WHERE date >= CURRENT_DATE - INTERVAL '20 days'
            ORDER BY date ASC, city ASC
        """)).fetchall()

        # --- Fuel history (for change features) ---
        fuel_hist = conn.execute(text("""
            SELECT date, lp_95, lp_92, lad, lsd, lk
            FROM fuel_prices
            ORDER BY date DESC LIMIT 60
        """)).fetchall()

        # --- Inflation history (for monthly deltas) ---
        inf_hist = conn.execute(text("""
            SELECT reference_month, ccpi_headline, ccpi_food
            FROM inflation_data
            ORDER BY reference_month DESC LIMIT 24
        """)).fetchall()

    # ── Build single-row feature dict ─────────────────────────────────────────
    row: dict = {}

    # Calendar
    row["year"]         = d.year
    row["month"]        = d.month
    row["day_of_week"]  = d.weekday()
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

    # Poya
    row["is_poya"]              = int(d in POYA_DATES)
    row["days_until_next_poya"] = days_until_next_poya(d)
    row["days_since_last_poya"] = days_since_last_poya(d)
    row["is_pre_poya"]          = int(row["days_until_next_poya"] in [1, 2])
    row["is_post_poya"]         = int(row["days_since_last_poya"] in [1, 2])

    # Macro
    if inf_hist:
        _, headline, food = inf_hist[0]
        row["Inflation_Rate"] = float(headline or 0.0)
        row["CCPI_Food"]      = float(food or 0.0)
    else:
        row["Inflation_Rate"] = 0.0
        row["CCPI_Food"]      = 0.0

    # Fuel
    if fuel_hist:
        _, lp95, lp92, lad, lsd, lk = fuel_hist[0]
        row["LP 95"] = float(lp95 or 0.0)
        row["LP 92"] = float(lp92 or 0.0)
        row["LAD"]   = float(lad or 0.0)
        row["LSD"]   = float(lsd or 0.0)
        row["LK"]    = float(lk or 0.0)
    else:
        row["LP 95"] = row["LP 92"] = row["LAD"] = row["LSD"] = row["LK"] = 0.0

    # Weather: latest per city + lagged aggregates from history
    if weather_hist:
        wh = pd.DataFrame(
            weather_hist,
            columns=["date", "city", "temp_mean_c", "wind_max_kmh", "gust_max_kmh", "precip_mm"],
        )
        wh["date"] = pd.to_datetime(wh["date"])
        wh = wh.sort_values(["date", "city"]).reset_index(drop=True)

        pivot = wh.pivot_table(
            index="date",
            columns="city",
            values=["temp_mean_c", "wind_max_kmh", "gust_max_kmh", "precip_mm"],
            aggfunc="mean",
        )
        metric_map = {
            "temp_mean_c": "temp_mean_C",
            "wind_max_kmh": "wind_max_kmh",
            "gust_max_kmh": "gust_max_kmh",
            "precip_mm": "precip_mm",
        }
        pivot.columns = [f"{city}_{metric_map.get(m, m)}" for m, city in pivot.columns]
        pivot = pivot.reset_index().sort_values("date").reset_index(drop=True)

        # Latest weather day (may be yesterday if today's not yet scraped)
        latest_weather = pivot.iloc[-1].to_dict()
        latest_weather.pop("date", None)
        row.update({k: float(v or 0.0) for k, v in latest_weather.items()})

        cities = wh["city"].unique().tolist()
        for suffix in ["temp_mean_C", "wind_max_kmh", "gust_max_kmh", "precip_mm"]:
            cols = [f"{c}_{suffix}" for c in cities if f"{c}_{suffix}" in pivot.columns]
            row[f"avg_{suffix}"] = float(pivot[cols].iloc[-1].mean()) if cols else 0.0
    else:
        row["avg_temp_mean_C"] = 0.0
        row["avg_wind_max_kmh"] = 0.0
        row["avg_gust_max_kmh"] = 0.0
        row["avg_precip_mm"] = 0.0

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

    # ── Exogenous change & regime features (mirror training) ───────────────
    # Fuel change features: computed from history (shift by 1 day)
    if "fuel_hist" in locals() and fuel_hist:
        fh = pd.DataFrame(fuel_hist, columns=["date", "lp_95", "lp_92", "lad", "lsd", "lk"])
        fh["date"] = pd.to_datetime(fh["date"])
        fh = fh.sort_values("date").reset_index(drop=True)
        for col_db, col in [("lp_95", "LP 95"), ("lp_92", "LP 92"), ("lad", "LAD"), ("lsd", "LSD"), ("lk", "LK")]:
            s = fh[col_db].astype(float).shift(1)
            row[f"{col}_chg_1d"] = float(s.diff(1).iloc[-1]) if len(s) >= 2 else 0.0
            row[f"{col}_chg_7d"] = float(s.diff(7).iloc[-1]) if len(s) >= 8 else 0.0
    else:
        for col in ["LP 95", "LP 92", "LAD", "LSD", "LK"]:
            row[f"{col}_chg_1d"] = 0.0
            row[f"{col}_chg_7d"] = 0.0

    # Inflation change features: latest month - previous month
    if "inf_hist" in locals() and inf_hist and len(inf_hist) >= 2:
        _, h1, f1 = inf_hist[0]
        _, h0, f0 = inf_hist[1]
        row["Inflation_Rate_chg_30d"] = float((h1 or 0.0) - (h0 or 0.0))
        row["CCPI_Food_chg_30d"] = float((f1 or 0.0) - (f0 or 0.0))
    else:
        row["Inflation_Rate_chg_30d"] = 0.0
        row["CCPI_Food_chg_30d"] = 0.0

    # Weather aggregates: shift by 1 day and compute rolling means/sums
    if "weather_hist" in locals() and weather_hist:
        # Reconstruct pivot again cheaply using already loaded history
        wh = pd.DataFrame(
            weather_hist,
            columns=["date", "city", "temp_mean_c", "wind_max_kmh", "gust_max_kmh", "precip_mm"],
        )
        wh["date"] = pd.to_datetime(wh["date"])
        wh = wh.sort_values(["date", "city"]).reset_index(drop=True)
        piv = wh.pivot_table(
            index="date",
            values=["temp_mean_c", "wind_max_kmh", "gust_max_kmh", "precip_mm"],
            aggfunc="mean",
        ).reset_index().sort_values("date").reset_index(drop=True)

        piv.rename(
            columns={
                "temp_mean_c": "avg_temp_mean_C",
                "wind_max_kmh": "avg_wind_max_kmh",
                "gust_max_kmh": "avg_gust_max_kmh",
                "precip_mm": "avg_precip_mm",
            },
            inplace=True,
        )

        for col in ["avg_temp_mean_C", "avg_wind_max_kmh", "avg_gust_max_kmh", "avg_precip_mm"]:
            s = piv[col].astype(float).shift(1)
            row[f"{col}_lag1"] = float(s.iloc[-1]) if len(s) else 0.0
            row[f"{col}_roll_mean_3"] = float(s.tail(3).mean()) if len(s) else 0.0
            row[f"{col}_roll_mean_7"] = float(s.tail(7).mean()) if len(s) else 0.0
            if "precip" in col:
                row[f"{col}_roll_sum_3"] = float(s.tail(3).sum()) if len(s) else 0.0
                row[f"{col}_roll_sum_7"] = float(s.tail(7).sum()) if len(s) else 0.0
    else:
        for col in ["avg_temp_mean_C", "avg_wind_max_kmh", "avg_gust_max_kmh", "avg_precip_mm"]:
            row[f"{col}_lag1"] = 0.0
            row[f"{col}_roll_mean_3"] = 0.0
            row[f"{col}_roll_mean_7"] = 0.0
        row["avg_precip_mm_roll_sum_3"] = 0.0
        row["avg_precip_mm_roll_sum_7"] = 0.0

    # Regime features from recent deltas (use past deltas; approximate training shift(1))
    deltas = pd.Series(np.diff(prices.astype(float)))
    prev = float(deltas.iloc[-2]) if len(deltas) >= 2 else 0.0
    tail7 = deltas.iloc[-8:-1] if len(deltas) >= 8 else deltas.iloc[:-1]
    tail30 = deltas.iloc[-31:-1] if len(deltas) >= 31 else deltas.iloc[:-1]
    std7 = float(tail7.std()) if len(tail7) > 1 else 0.0
    std30 = float(tail30.std()) if len(tail30) > 1 else 0.0
    row["delta_roll_std_7"] = std7
    row["delta_roll_std_30"] = std30
    row["shock_1d"] = int(abs(prev) > (1.5 * (std30 + 1e-9)))

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
