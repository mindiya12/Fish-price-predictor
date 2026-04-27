"""
Train Models - Phase 2: Ensemble (XGBoost + LightGBM) + Early Stopping + CV
=============================================================================
Phase 2 additions:
  - LightGBM trained per horizon alongside XGBoost
  - XGBoost early stopping (no more overfitting on 1500 trees)
  - TimeSeriesSplit (5-fold) CV for realistic out-of-sample evaluation
  - Blend updated: 45% XGB + 45% LGBM + 10% rolling-baseline (row-wise)
  - Per-model metrics reported separately then combined
"""

import os, sys, joblib, warnings
import pandas as pd
import numpy as np
from datetime import date
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poya_days import POYA_DATES, days_until_next_poya, days_since_last_poya

warnings.filterwarnings("ignore")

DATABASE_URL = os.environ.get("DATABASE_URL")
FISH         = os.environ.get("FISH", "balaya")
LOCATION     = os.environ.get("LOCATION", "peliyagoda")
MODELS_DIR   = os.environ.get("MODELS_DIR", "/app/models")
RUN_HEAVY_EVAL = os.environ.get("RUN_HEAVY_EVAL", "0").lower() in ("1", "true", "yes", "y")
CV_SPLITS      = int(os.environ.get("CV_SPLITS", "5"))
BACKTEST_WIN   = int(os.environ.get("BACKTEST_WIN", "30"))
BACKTEST_STEP  = int(os.environ.get("BACKTEST_STEP", "15"))

# Phase 2 blend: 45% XGB + 45% LGBM + 10% baseline (row-wise)
XGB_WEIGHT   = 0.45
LGBM_WEIGHT  = 0.45
BASE_WEIGHT  = 0.10

XGB_PARAMS = {
    "n_estimators":     2000,   # higher ceiling, early stopping controls final count
    "max_depth":        6,
    "learning_rate":    0.02,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "reg_alpha":        0.01,
    "reg_lambda":       2.0,
    "random_state":     42,
    "n_jobs":           -1,
    "early_stopping_rounds": 50,
    # Robust to spikes; improves MAE in practice for jumpy series
    "objective":        "reg:pseudohubererror",
    "eval_metric":      "rmse",
}

LGBM_PARAMS = {
    "n_estimators":     2000,
    "max_depth":        6,
    "learning_rate":    0.02,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "min_child_samples":20,
    "reg_alpha":        0.01,
    "reg_lambda":       2.0,
    "random_state":     42,
    "n_jobs":           -1,
    "verbose":          -1,
    "objective":        "huber",
}

TARGET_COL      = "price"
COLS_TO_EXCLUDE = ["date", "season", TARGET_COL]


# ── DATA LOADING (same as Phase 1) ────────────────────────────────────────────

def load_training_data(engine) -> pd.DataFrame:
    print("Loading price history...")
    price_df = pd.read_sql(text(
        "SELECT date, price FROM price_history WHERE fish=:fish AND location=:location ORDER BY date"
    ), engine, params={"fish": FISH, "location": LOCATION})
    price_df["date"] = pd.to_datetime(price_df["date"])

    print("Loading weather data...")
    weather_df = pd.read_sql(text(
        "SELECT date, city, temp_mean_c, wind_max_kmh, gust_max_kmh, precip_mm FROM weather_data ORDER BY date, city"
    ), engine)
    weather_df["date"] = pd.to_datetime(weather_df["date"])
    weather_pivot = weather_df.pivot_table(
        index="date", columns="city",
        values=["temp_mean_c","wind_max_kmh","gust_max_kmh","precip_mm"], aggfunc="mean"
    )
    metric_map = {"temp_mean_c":"temp_mean_C","wind_max_kmh":"wind_max_kmh","gust_max_kmh":"gust_max_kmh","precip_mm":"precip_mm"}
    weather_pivot.columns = [f"{city}_{metric_map.get(m,m)}" for m,city in weather_pivot.columns]
    weather_pivot = weather_pivot.reset_index()
    cities = weather_df["city"].unique().tolist()
    for agg, suffix in [("mean","temp_mean_C"),("mean","wind_max_kmh"),("mean","gust_max_kmh"),("mean","precip_mm")]:
        cols = [f"{c}_{suffix}" for c in cities if f"{c}_{suffix}" in weather_pivot.columns]
        weather_pivot[f"avg_{suffix}"] = weather_pivot[cols].mean(axis=1) if cols else 0.0

    print("Loading fuel & inflation...")
    fuel_df = pd.read_sql(text("SELECT date, lp_95, lp_92, lad, lsd, lk FROM fuel_prices ORDER BY date"), engine)
    fuel_df["date"] = pd.to_datetime(fuel_df["date"])
    fuel_df.rename(columns={"lp_95":"LP 95","lp_92":"LP 92","lad":"LAD","lsd":"LSD","lk":"LK"}, inplace=True)

    inf_df = pd.read_sql(text("SELECT reference_month, ccpi_headline, ccpi_food FROM inflation_data ORDER BY reference_month"), engine)
    inf_df["date"] = pd.to_datetime(inf_df["reference_month"])
    inf_df.rename(columns={"ccpi_headline":"Inflation_Rate","ccpi_food":"CCPI_Food"}, inplace=True)

    df = price_df.merge(weather_pivot, on="date", how="left")
    df = df.merge(fuel_df, on="date", how="left")
    df["ym"] = df["date"].dt.to_period("M").dt.to_timestamp()
    inf_df["ym"] = inf_df["date"].dt.to_period("M").dt.to_timestamp()
    df = df.merge(inf_df[["ym","Inflation_Rate","CCPI_Food"]], on="ym", how="left").drop("ym", axis=1)
    for col in ["LP 95","LP 92","LAD","LSD","LK","Inflation_Rate","CCPI_Food"]:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()

    # Guardrails: prevent bad scraped macro values (e.g., year parsed as inflation)
    for col in ["Inflation_Rate", "CCPI_Food"]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            s = s.where((s >= -100) & (s <= 100), np.nan)
            df[col] = s.ffill().bfill().fillna(0.0)

    # Calendar
    df["year"]         = df["date"].dt.year
    df["month"]        = df["date"].dt.month
    df["day_of_week"]  = df["date"].dt.dayofweek
    df["quarter"]      = df["date"].dt.quarter
    df["day_of_year"]  = df["date"].dt.dayofyear
    df["day_of_month"] = df["date"].dt.day
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    # Cyclic encoding
    df["sin_month"]    = np.sin(2*np.pi*df["month"]/12)
    df["cos_month"]    = np.cos(2*np.pi*df["month"]/12)
    df["sin_day_year"] = np.sin(2*np.pi*df["day_of_year"]/365)
    df["cos_day_year"] = np.cos(2*np.pi*df["day_of_year"]/365)
    df["sin_week"]     = np.sin(2*np.pi*df["week_of_year"]/52)
    df["cos_week"]     = np.cos(2*np.pi*df["week_of_year"]/52)

    # Poya features
    date_col = df["date"].dt.date
    df["is_poya"]               = date_col.isin(POYA_DATES).astype(int)
    df["days_until_next_poya"]  = date_col.apply(days_until_next_poya)
    df["days_since_last_poya"]  = date_col.apply(days_since_last_poya)
    df["is_pre_poya"]           = df["days_until_next_poya"].isin([1,2]).astype(int)
    df["is_post_poya"]          = df["days_since_last_poya"].isin([1,2]).astype(int)

    # Extended lags
    for lag in [1,2,3,5,7,14,21,30]:
        df[f"price_lag{lag}"] = df["price"].shift(lag)

    # Rolling stats
    p = df["price"].shift(1)
    for w in [3,7,14,30]:
        df[f"price_roll_mean_{w}"] = p.rolling(w).mean()
        df[f"price_roll_std_{w}"]  = p.rolling(w).std()
        df[f"price_roll_min_{w}"]  = p.rolling(w).min()
        df[f"price_roll_max_{w}"]  = p.rolling(w).max()
        df[f"price_roll_range_{w}"]= df[f"price_roll_max_{w}"] - df[f"price_roll_min_{w}"]

    # EWM
    df["price_ewm7"]  = p.ewm(span=7,  adjust=False).mean()
    df["price_ewm14"] = p.ewm(span=14, adjust=False).mean()
    df["price_ewm30"] = p.ewm(span=30, adjust=False).mean()

    # Momentum
    df["price_change"]            = df["price"] - df["price_lag1"]
    df["price_change_1d"]         = df["price_change"]
    df["price_change_7d"]         = df["price"] - df["price_lag7"]
    df["price_change_14d"]        = df["price"] - df["price_lag14"]
    df["price_pct_change_1d"]     = df["price"].pct_change(1)
    df["price_pct_change_7d"]     = df["price"].pct_change(7)
    df["price_acceleration"]      = df["price_change_1d"] - df["price_change_1d"].shift(1)
    df["price_dev_from_7d"]       = df["price_lag1"] - df["price_roll_mean_7"]
    df["price_dev_from_30d"]      = df["price_lag1"] - df["price_roll_mean_30"]
    df["price_trend_ratio_7_30"]  = df["price_roll_mean_7"] / (df["price_roll_mean_30"] + 1e-9)
    df["price_volatility_7d"]     = p.rolling(7).std()
    df["price_volatility_30d"]    = p.rolling(30).std()

    # ── Exogenous change features (focus on "between two dates") ────────────
    # Use shifted(1) to ensure only past info at time t.
    exog_shift = 1

    # Fuel deltas (1d, 7d)
    for col in ["LP 95", "LP 92", "LAD", "LSD", "LK"]:
        if col in df.columns:
            s = df[col].shift(exog_shift)
            df[f"{col}_chg_1d"] = s.diff(1)
            df[f"{col}_chg_7d"] = s.diff(7)

    # Inflation changes (month-to-month proxy; daily forward-filled)
    for col in ["Inflation_Rate", "CCPI_Food"]:
        if col in df.columns:
            s = df[col].shift(exog_shift)
            df[f"{col}_chg_30d"] = s.diff(30)

    # Weather aggregates on avg_* signals (lagged + rolling)
    for col in ["avg_temp_mean_C", "avg_wind_max_kmh", "avg_gust_max_kmh", "avg_precip_mm"]:
        if col in df.columns:
            s = df[col].shift(exog_shift)
            df[f"{col}_lag1"] = s.shift(0)
            df[f"{col}_roll_mean_3"] = s.rolling(3).mean()
            df[f"{col}_roll_mean_7"] = s.rolling(7).mean()
            if "precip" in col:
                df[f"{col}_roll_sum_3"] = s.rolling(3).sum()
                df[f"{col}_roll_sum_7"] = s.rolling(7).sum()

    # Regime: delta-volatility and shock flags
    d1 = df["price_change_1d"].shift(1)
    df["delta_roll_std_7"]  = d1.rolling(7).std()
    df["delta_roll_std_30"] = d1.rolling(30).std()
    df["shock_1d"] = (d1.abs() > (1.5 * (df["delta_roll_std_30"] + 1e-9))).astype(int)

    # ── ENHANCED FEATURE ENGINEERING (Phase 2.5) ──────────────────────────────
    # These features focus on capturing price change patterns and regimes
    
    # 1. Non-linear price change indicators
    df["price_change_squared"]     = df["price_change_1d"] ** 2  # Magnitude of shocks
    df["price_change_abs"]         = np.abs(df["price_change_1d"])
    df["price_change_sign_switch"] = (df["price_change_1d"] * df["price_change_1d"].shift(1) < 0).astype(int)  # Direction reversal
    
    # 2. Adaptive momentum (weighted by volatility regime)
    vol_30 = df["price_volatility_30d"]
    df["adaptive_momentum_1d"]  = df["price_change_1d"] / (vol_30 + 1e-9)  # Normalized by volatility
    df["adaptive_momentum_7d"]  = df["price_change_7d"] / (vol_30 + 1e-9)
    df["price_momentum_ratio"]  = (df["price_change_7d"] + 1e-9) / (df["price_change_1d"].abs() + 1e-9)  # Ratio of trends
    
    # 3. Acceleration features (2nd derivative of price)
    df["price_acceleration_abs"]  = np.abs(df["price_acceleration"])
    df["price_accel_signed"]      = df["price_acceleration"]  # Keep sign for direction
    df["acceleration_momentum"]   = df["price_acceleration"] * df["price_change_1d"]  # Interaction
    
    # 4. Mean reversion indicators (how far from equilibrium)
    df["price_drawdown_7d"]   = (df["price_roll_max_7"] - df["price_lag1"]) / (df["price_roll_range_7"] + 1e-9)  # 0=at min, 1=at max
    df["price_drawup_7d"]     = (df["price_lag1"] - df["price_roll_min_7"]) / (df["price_roll_range_7"] + 1e-9)
    df["price_drawdown_30d"]  = (df["price_roll_max_30"] - df["price_lag1"]) / (df["price_roll_range_30"] + 1e-9)
    df["price_drawup_30d"]    = (df["price_lag1"] - df["price_roll_min_30"]) / (df["price_roll_range_30"] + 1e-9)
    
    # 5. Volatility regime flags
    vol_7_p75 = df["price_volatility_7d"].quantile(0.75)
    vol_7_p90 = df["price_volatility_7d"].quantile(0.90)
    df["high_volatility_flag"]     = (df["price_volatility_7d"] > vol_7_p75).astype(int)
    df["extreme_volatility_flag"]  = (df["price_volatility_7d"] > vol_7_p90).astype(int)
    df["vol_increasing"]           = (df["price_volatility_7d"] > df["price_volatility_7d"].shift(7)).astype(int)
    
    # 6. Shock duration and recovery
    shock_series = d1.abs() > (1.5 * (df["delta_roll_std_30"] + 1e-9))
    shock_groups = (shock_series != shock_series.shift()).cumsum()
    df["shock_duration"] = shock_series.groupby(shock_groups).cumsum()
    df["shock_duration"] = df["shock_duration"] * shock_series  # Zero out non-shock periods
    df["days_since_shock"] = (~shock_series).groupby((~shock_series) != (~shock_series).shift()).cumsum()
    df["days_since_shock"] = df["days_since_shock"] * (~shock_series)  # Zero out shock periods
    
    # 7. Cross-feature interactions (Price × Seasonality)
    df["price_lag1_x_sin_month"]  = df["price_lag1"] * df["sin_month"]
    df["price_lag1_x_cos_month"]  = df["price_lag1"] * df["cos_month"]
    df["price_lag1_x_is_poya"]    = df["price_lag1"] * df["is_poya"]
    df["price_lag1_x_is_pre_poya"] = df["price_lag1"] * df["is_pre_poya"]
    df["change_x_day_of_week"]    = df["price_change_1d"] * (df["day_of_week"] - 2.5)  # Centered day_of_week
    
    # 8. Volatility × Macro interactions (better capture shock amplification)
    if "LP 95" in df.columns and "LP 92" in df.columns:
        lp95_pct_change = df["LP 95"].pct_change(1).fillna(0)
        df["volatility_x_fuel_change"] = df["price_volatility_7d"] * lp95_pct_change
    
    if "Inflation_Rate" in df.columns:
        df["volatility_x_inflation"] = df["price_volatility_7d"] * (df["Inflation_Rate"] / 100.0 + 1e-9)
    
    if "avg_precip_mm" in df.columns:
        df["precip_x_momentum"] = df["avg_precip_mm"] * df["price_change_1d"]
    
    # 9. Market sentiment indicators
    df["velocity_of_change"] = df["price_change_1d"] - df["price_change_1d"].shift(1)  # Rate of change of momentum
    df["consecutive_up_days"]  = ((df["price_change_1d"] > 0).astype(int) * 
                                  ((df["price_change_1d"] > 0) == (df["price_change_1d"].shift(1) > 0)).astype(int)).rolling(7).sum()
    df["consecutive_down_days"] = ((df["price_change_1d"] < 0).astype(int) * 
                                   ((df["price_change_1d"] < 0) == (df["price_change_1d"].shift(1) < 0)).astype(int)).rolling(7).sum()
    
    # 10. Lag interaction with volatility (recent history weighted by risk)
    df["price_lag1_weighted_vol"] = df["price_lag1"] * df["price_volatility_7d"]
    df["price_lag7_weighted_vol"] = df["price_lag7"] * df["price_volatility_7d"]
    
    # 11. EWM momentum (exponentially weighted momentum)
    df["momentum_ewm7"]  = df["price_change_1d"].ewm(span=7, adjust=False).mean()
    df["momentum_ewm14"] = df["price_change_1d"].ewm(span=14, adjust=False).mean()
    
    # 12. Unexpected change detection (residual from macro explanations)
    if "LP 95_chg_1d" in df.columns and "avg_precip_mm_lag1" in df.columns:
        # Simple model: expected change from fuel + weather
        df["expected_change_macro"] = (0.5 * df["LP 95_chg_1d"] + 0.1 * df["avg_precip_mm_lag1"])
        df["unexpected_change"] = df["price_change_1d"] - df["expected_change_macro"]

    df = df.dropna(subset=["price_lag1","price_lag7","price_lag30"]).reset_index(drop=True)
    print(f"Training data: {len(df)} rows | {df['is_poya'].sum()} Poya days | {len(df.columns)} cols")
    return df


def clean_data(df, feats):
    for col in feats:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())
    return df


def get_feature_cols(df):
    core = [
        'year','month','day_of_week','day_of_year','quarter','day_of_month','week_of_year',
        'sin_month','cos_month','sin_day_year','cos_day_year','sin_week','cos_week',
        'is_poya','days_until_next_poya','days_since_last_poya','is_pre_poya','is_post_poya',
        'Inflation_Rate','CCPI_Food','LP 95','LP 92','LAD','LSD','LK',
        'Matara_temp_mean_C','Matara_wind_max_kmh','Matara_gust_max_kmh','Matara_precip_mm',
        'Galle_temp_mean_C','Galle_wind_max_kmh','Galle_gust_max_kmh','Galle_precip_mm',
        'Negombo_temp_mean_C','Negombo_wind_max_kmh','Negombo_gust_max_kmh','Negombo_precip_mm',
        'Kalutara_temp_mean_C','Kalutara_precip_mm','Kalutara_wind_max_kmh','Kalutara_gust_max_kmh',
        'Tangalla_temp_mean_C','Tangalla_wind_max_kmh','Tangalla_gust_max_kmh','Tangalla_precip_mm',
        'avg_temp_mean_C','avg_wind_max_kmh','avg_gust_max_kmh','avg_precip_mm',
        'price_lag1','price_lag2','price_lag3','price_lag5','price_lag7','price_lag14','price_lag21','price_lag30',
        'price_roll_mean_3','price_roll_std_3','price_roll_min_3','price_roll_max_3','price_roll_range_3',
        'price_roll_mean_7','price_roll_std_7','price_roll_min_7','price_roll_max_7','price_roll_range_7',
        'price_roll_mean_14','price_roll_std_14','price_roll_min_14','price_roll_max_14','price_roll_range_14',
        'price_roll_mean_30','price_roll_std_30','price_roll_min_30','price_roll_max_30','price_roll_range_30',
        'price_ewm7','price_ewm14','price_ewm30',
        'price_change','price_change_1d','price_change_7d','price_change_14d',
        'price_pct_change_1d','price_pct_change_7d','price_acceleration',
        'price_dev_from_7d','price_dev_from_30d','price_trend_ratio_7_30',
        'price_volatility_7d','price_volatility_30d',
        # Exogenous change/regime features (added above; included if present)
        'LP 95_chg_1d','LP 95_chg_7d','LP 92_chg_1d','LP 92_chg_7d','LAD_chg_1d','LAD_chg_7d','LSD_chg_1d','LSD_chg_7d','LK_chg_1d','LK_chg_7d',
        'Inflation_Rate_chg_30d','CCPI_Food_chg_30d',
        'avg_temp_mean_C_lag1','avg_temp_mean_C_roll_mean_3','avg_temp_mean_C_roll_mean_7',
        'avg_wind_max_kmh_lag1','avg_wind_max_kmh_roll_mean_3','avg_wind_max_kmh_roll_mean_7',
        'avg_gust_max_kmh_lag1','avg_gust_max_kmh_roll_mean_3','avg_gust_max_kmh_roll_mean_7',
        'avg_precip_mm_lag1','avg_precip_mm_roll_mean_3','avg_precip_mm_roll_mean_7','avg_precip_mm_roll_sum_3','avg_precip_mm_roll_sum_7',
        'delta_roll_std_7','delta_roll_std_30','shock_1d',
        # ──── ENHANCED FEATURES (Phase 2.5) ────
        # Non-linear price change indicators
        'price_change_squared','price_change_abs','price_change_sign_switch',
        # Adaptive momentum (volatility-normalized)
        'adaptive_momentum_1d','adaptive_momentum_7d','price_momentum_ratio',
        # Acceleration features (2nd derivative)
        'price_acceleration_abs','price_accel_signed','acceleration_momentum',
        # Mean reversion indicators (position in range)
        'price_drawdown_7d','price_drawup_7d','price_drawdown_30d','price_drawup_30d',
        # Volatility regime flags
        'high_volatility_flag','extreme_volatility_flag','vol_increasing',
        # Shock duration and recovery
        'shock_duration','days_since_shock',
        # Cross-feature interactions (Price × Seasonality)
        'price_lag1_x_sin_month','price_lag1_x_cos_month','price_lag1_x_is_poya','price_lag1_x_is_pre_poya',
        'change_x_day_of_week',
        # Volatility × Macro interactions
        'volatility_x_fuel_change','volatility_x_inflation','precip_x_momentum',
        # Market sentiment indicators
        'velocity_of_change','consecutive_up_days','consecutive_down_days',
        # Lag interactions with volatility
        'price_lag1_weighted_vol','price_lag7_weighted_vol',
        # EWM momentum
        'momentum_ewm7','momentum_ewm14',
        # Unexpected change
        'expected_change_macro','unexpected_change',
    ]
    available = [c for c in core if c in df.columns]
    extra = [c for c in df.columns if c not in COLS_TO_EXCLUDE + ["date","ym"] and c not in available]
    return available + extra


def rolling_backtest(df: pd.DataFrame, feature_cols: list[str], horizon: int, window: int = 30, step: int = 15, min_train: int = 240):
    """
    Rolling-origin backtest on the *tail* of the dataset.
    Evaluates absolute price error while training on delta targets.
    """
    y_abs = df[TARGET_COL].shift(-horizon)
    y_delta = (df[TARGET_COL].shift(-horizon) - df[TARGET_COL])
    base = df[TARGET_COL].astype(float).values

    # Only consider rows where label exists
    valid = y_abs.notna()
    idx = np.where(valid.values)[0]
    if len(idx) < (min_train + window):
        return None

    start = max(min_train, idx[0])
    end = idx[-1] - window + 1
    starts = list(range(start, end, step))
    rmses, maes = [], []

    for s in starts:
        tr_end = s
        te_end = s + window
        tr = df.iloc[:tr_end].copy()
        te = df.iloc[tr_end:te_end].copy()

        tr = clean_data(tr, feature_cols)
        te = clean_data(te, feature_cols)

        y_tr = y_delta.iloc[:tr_end].dropna()
        X_tr = tr[feature_cols].iloc[:len(y_tr)]
        y_te_abs = y_abs.iloc[tr_end:te_end].dropna()
        X_te = te[feature_cols].iloc[:len(y_te_abs)]
        base_te = base[tr_end:tr_end + len(y_te_abs)]

        val_size = max(15, int(len(X_tr) * 0.1))
        X_tr2, X_es = X_tr.iloc[:-val_size], X_tr.iloc[-val_size:]
        y_tr2, y_es = y_tr.iloc[:-val_size], y_tr.iloc[-val_size:]

        xgb = XGBRegressor(**XGB_PARAMS)
        xgb.fit(X_tr2, y_tr2, eval_set=[(X_es, y_es)], verbose=False)

        lgbm = LGBMRegressor(**LGBM_PARAMS)
        lgbm.fit(
            X_tr2, y_tr2,
            eval_set=[(X_es, y_es)],
            callbacks=[
                __import__("lightgbm").early_stopping(stopping_rounds=50, verbose=False),
                __import__("lightgbm").log_evaluation(period=-1),
            ]
        )

        dx = xgb.predict(X_te)
        dl = lgbm.predict(X_te)
        baseline_delta = (te["price_roll_mean_7"].iloc[:len(y_te_abs)].astype(float).values - base_te) if "price_roll_mean_7" in te.columns else 0.0
        d = XGB_WEIGHT * dx + LGBM_WEIGHT * dl + BASE_WEIGHT * baseline_delta
        pred_abs = base_te + d

        rmses.append(float(np.sqrt(mean_squared_error(y_te_abs, pred_abs))))
        maes.append(float(mean_absolute_error(y_te_abs, pred_abs)))

    return {
        "windows": len(starts),
        "rmse_mean": float(np.mean(rmses)) if rmses else None,
        "mae_mean": float(np.mean(maes)) if maes else None,
        "rmse_std": float(np.std(rmses)) if rmses else None,
        "mae_std": float(np.std(maes)) if maes else None,
    }


# ── PHASE 2: TIME-SERIES CROSS-VALIDATION ─────────────────────────────────────

def run_tscv(X, y, xgb_params, lgbm_params, n_splits=5):
    """
    Walk-forward TimeSeriesSplit CV. Returns mean RMSE and MAPE for XGB and LGBM.
    Uses a gap=3 to avoid leakage between train and validation folds.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits, gap=3)
    xgb_rmses, lgbm_rmses = [], []
    xgb_mapes, lgbm_mapes = [], []

    for fold, (tr_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_tr, X_val = X.iloc[tr_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[tr_idx], y.iloc[val_idx]

        # XGBoost with early stopping — needs a validation set carved from train
        val_size = max(10, int(len(X_tr) * 0.1))
        X_tr2, X_es = X_tr.iloc[:-val_size], X_tr.iloc[-val_size:]
        y_tr2, y_es = y_tr.iloc[:-val_size], y_tr.iloc[-val_size:]

        xgb_cv = XGBRegressor(**xgb_params)
        xgb_cv.fit(X_tr2, y_tr2, eval_set=[(X_es, y_es)], verbose=False)
        xgb_pred = xgb_cv.predict(X_val)

        lgbm_cv = LGBMRegressor(**lgbm_params)
        lgbm_cv.fit(X_tr, y_tr, eval_set=[(X_val, y_val)],
                    callbacks=[])
        lgbm_pred = lgbm_cv.predict(X_val)

        xgb_rmses.append(np.sqrt(mean_squared_error(y_val, xgb_pred)))
        lgbm_rmses.append(np.sqrt(mean_squared_error(y_val, lgbm_pred)))
        xgb_mapes.append(mean_absolute_percentage_error(y_val, xgb_pred)*100)
        lgbm_mapes.append(mean_absolute_percentage_error(y_val, lgbm_pred)*100)
        print(f"    Fold {fold}: XGB RMSE={xgb_rmses[-1]:.1f} MAPE={xgb_mapes[-1]:.2f}%  |  LGBM RMSE={lgbm_rmses[-1]:.1f} MAPE={lgbm_mapes[-1]:.2f}%")

    return {
        "xgb_cv_rmse":  float(np.mean(xgb_rmses)),
        "lgbm_cv_rmse": float(np.mean(lgbm_rmses)),
        "xgb_cv_mape":  float(np.mean(xgb_mapes)),
        "lgbm_cv_mape": float(np.mean(lgbm_mapes)),
    }


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(DATABASE_URL)
    df = load_training_data(engine)
    feature_cols = get_feature_cols(df)
    print(f"\nUsing {len(feature_cols)} features")
    print(f"Target: Δ(price) per horizon (price[t+h] - price[t])")
    print(f"Blend: XGB×{XGB_WEIGHT}  LGBM×{LGBM_WEIGHT}  BASE×{BASE_WEIGHT}\n")
    print(f"Heavy eval (CV+backtest): {'ON' if RUN_HEAVY_EVAL else 'OFF'}")

    test_size = 30
    train_df = df.iloc[:-test_size].copy()
    test_df  = df.iloc[-test_size:].copy()
    train_df = clean_data(train_df, feature_cols)
    test_df  = clean_data(test_df,  feature_cols)

    print(f"Train: {len(train_df)} rows | Test: {len(test_df)} rows")

    os.makedirs(MODELS_DIR, exist_ok=True)
    xgb_models, lgbm_models = {}, {}
    metrics = []

    for h in range(1, 4):
        print(f"\n{'='*50}")
        print(f"  Horizon h={h}")
        print(f"{'='*50}")

        # Train on delta: price[t+h] - price[t]
        y_train_full = (train_df[TARGET_COL].shift(-h) - train_df[TARGET_COL]).dropna()
        X_train_full = train_df[feature_cols].iloc[:len(y_train_full)]
        # Holdout labels (delta and absolute)
        y_test       = (test_df[TARGET_COL].shift(-h) - test_df[TARGET_COL]).dropna()
        X_test       = test_df[feature_cols].iloc[:len(y_test)]
        y_test_abs   = test_df[TARGET_COL].shift(-h).dropna()
        base_price   = test_df[TARGET_COL].iloc[:len(y_test_abs)].astype(float).values

        cv_results = {"xgb_cv_rmse": 0.0, "lgbm_cv_rmse": 0.0, "xgb_cv_mape": 0.0, "lgbm_cv_mape": 0.0}
        if RUN_HEAVY_EVAL:
            # ── Phase 2: TimeSeriesSplit CV ───────────────────────────────────
            print(f"\n  [CV] Running {CV_SPLITS}-fold TimeSeriesSplit...")
            cv_results = run_tscv(X_train_full, y_train_full, XGB_PARAMS, LGBM_PARAMS, n_splits=CV_SPLITS)
            print(f"\n  CV Summary:")
            print(f"    XGB  → CV RMSE={cv_results['xgb_cv_rmse']:.2f}  CV MAPE={cv_results['xgb_cv_mape']:.2f}%")
            print(f"    LGBM → CV RMSE={cv_results['lgbm_cv_rmse']:.2f}  CV MAPE={cv_results['lgbm_cv_mape']:.2f}%")

            # ── Rolling backtest (more stable than single 30d holdout) ───────
            bt = rolling_backtest(df, feature_cols, horizon=h, window=BACKTEST_WIN, step=BACKTEST_STEP, min_train=240)
            if bt and bt["rmse_mean"] is not None:
                print(f"\n  [Backtest] {bt['windows']} windows: RMSE={bt['rmse_mean']:.2f}±{bt['rmse_std']:.2f}  MAE={bt['mae_mean']:.2f}±{bt['mae_std']:.2f}")

        # ── Phase 2: XGBoost with early stopping ─────────────────────────────
        print(f"\n  [XGB] Training with early stopping...")
        val_size = max(15, int(len(X_train_full) * 0.1))
        X_tr, X_val_es = X_train_full.iloc[:-val_size], X_train_full.iloc[-val_size:]
        y_tr, y_val_es = y_train_full.iloc[:-val_size], y_train_full.iloc[-val_size:]

        xgb_model = XGBRegressor(**XGB_PARAMS)
        xgb_model.fit(X_tr, y_tr, eval_set=[(X_val_es, y_val_es)], verbose=False)
        best_trees = xgb_model.best_iteration
        print(f"    Best iteration: {best_trees} trees (of {XGB_PARAMS['n_estimators']} max)")

        # ── Phase 2: LightGBM ─────────────────────────────────────────────────
        print(f"\n  [LGBM] Training LightGBM...")
        lgbm_model = LGBMRegressor(**LGBM_PARAMS)
        lgbm_model.fit(
            X_tr, y_tr,
            eval_set=[(X_val_es, y_val_es)],
            callbacks=[
                __import__("lightgbm").early_stopping(stopping_rounds=50, verbose=False),
                __import__("lightgbm").log_evaluation(period=-1),
            ]
        )
        print(f"    Best iteration: {lgbm_model.best_iteration_} trees")

        # ── Holdout evaluation ────────────────────────────────────────────────
        if len(y_test) > 0 and len(y_test_abs) > 0:
            xgb_delta  = xgb_model.predict(X_test)
            lgbm_delta = lgbm_model.predict(X_test)

            # Row-wise baseline: (rolling mean 7 - today's price) as delta
            # price_roll_mean_7 is computed from shifted series (excludes current price), safe at time t.
            if "price_roll_mean_7" in test_df.columns:
                baseline_delta = (test_df["price_roll_mean_7"].iloc[:len(y_test_abs)].astype(float).values - base_price)
            else:
                baseline_delta = np.zeros_like(base_price, dtype=float)

            ens_delta = XGB_WEIGHT * xgb_delta + LGBM_WEIGHT * lgbm_delta + BASE_WEIGHT * baseline_delta

            # Convert delta predictions back to absolute price for reporting/storing metrics
            xgb_preds  = base_price + xgb_delta
            lgbm_preds = base_price + lgbm_delta
            ens_preds  = base_price + ens_delta

            def metrics_row(name, preds):
                rmse = float(np.sqrt(mean_squared_error(y_test_abs, preds)))
                mae  = float(mean_absolute_error(y_test_abs, preds))
                mape = float(mean_absolute_percentage_error(y_test_abs, preds)*100)
                r2   = float(r2_score(y_test_abs, preds))
                print(f"    {name:10s}: RMSE={rmse:.2f}  MAE={mae:.2f}  MAPE={mape:.2f}%  R²={r2:.3f}")
                return rmse, mae, mape, r2

            print(f"\n  Holdout metrics:")
            metrics_row("XGB", xgb_preds)
            metrics_row("LGBM", lgbm_preds)
            rmse, mae, mape, r2 = metrics_row("Ensemble", ens_preds)
        else:
            rmse, mae, mape, r2 = 0.0, 0.0, 0.0, 0.0

        # Save models
        xgb_path  = os.path.join(MODELS_DIR, f"{FISH}_h{h}.pkl")
        lgbm_path = os.path.join(MODELS_DIR, f"{FISH}_h{h}_lgbm.pkl")
        feat_path = os.path.join(MODELS_DIR, f"{FISH}_h{h}_features.pkl")
        joblib.dump(xgb_model,    xgb_path)
        joblib.dump(lgbm_model,   lgbm_path)
        joblib.dump(feature_cols, feat_path)
        print(f"\n  Saved: {xgb_path}")
        print(f"  Saved: {lgbm_path}")

        xgb_models[h]  = xgb_model
        lgbm_models[h] = lgbm_model
        metrics.append({
            "horizon": h, "rmse": rmse, "mae": mae, "mape": mape, "r2": r2,
            **cv_results
        })

    # ── Save metrics to DB ─────────────────────────────────────────────────────
    model_version = f"ensemble_p2_delta_{pd.Timestamp.now().strftime('%Y%m%d')}"
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE model_metrics SET is_production=FALSE WHERE fish=:fish AND location=:location"
        ), {"fish": FISH, "location": LOCATION})
        for m in metrics:
            conn.execute(text("""
                INSERT INTO model_metrics (model_version, horizon, rmse, mae, mape, r2_score, xgb_weight, fish, location, is_production)
                VALUES (:ver, :h, :rmse, :mae, :mape, :r2, :w, :fish, :loc, TRUE)
                ON CONFLICT (model_version, horizon, fish, location) DO UPDATE
                SET rmse=EXCLUDED.rmse, mae=EXCLUDED.mae, mape=EXCLUDED.mape,
                    r2_score=EXCLUDED.r2_score, xgb_weight=EXCLUDED.xgb_weight,
                    is_production=EXCLUDED.is_production, trained_at=NOW()
            """), {"ver": model_version, "h": m["horizon"], "rmse": m["rmse"],
                   "mae": m["mae"], "mape": m["mape"], "r2": m["r2"],
                   "w": XGB_WEIGHT, "fish": FISH, "loc": LOCATION})

    print(f"\n{'='*50}")
    print(f"✅ Phase 2 training complete. Version: {model_version}")
    print(f"{'='*50}")
    print("\nFinal ensemble holdout metrics:")
    for m in metrics:
        print(f"  h={m['horizon']}: RMSE={m['rmse']:.2f}  MAE={m['mae']:.2f}  MAPE={m['mape']:.2f}%  R²={m['r2']:.3f}")

    # ── Generate blended forecasts ─────────────────────────────────────────────
    last_row = test_df.iloc[[-1]]
    print(f"\nGenerating 3-day ensemble forecast (delta-target):")

    with engine.begin() as conn:
        for h in range(1, 4):
            base_today = float(last_row["price"].iloc[0])
            baseline_delta = float((last_row["price_roll_mean_7"].iloc[0] - base_today)) if "price_roll_mean_7" in last_row.columns else 0.0

            xgb_delta  = float(xgb_models[h].predict(last_row[feature_cols])[0])
            lgbm_delta = float(lgbm_models[h].predict(last_row[feature_cols])[0])
            blended_delta = XGB_WEIGHT * xgb_delta + LGBM_WEIGHT * lgbm_delta + BASE_WEIGHT * baseline_delta
            blended = base_today + blended_delta
            rmse_h    = next(m["rmse"] for m in metrics if m["horizon"] == h)
            lo, hi    = blended - rmse_h, blended + rmse_h
            target    = (df["date"].iloc[-1] + pd.Timedelta(days=h)).date()

            print(f"  h={h} ({target}): ΔXGB={xgb_delta:+.1f}  ΔLGBM={lgbm_delta:+.1f}  Price={blended:.1f}  CI=[{lo:.0f},{hi:.0f}]")
            conn.execute(text("""
                INSERT INTO forecasts (forecast_date, horizon, blended_prediction, conf_lower, conf_upper, model_version, fish, location)
                VALUES (:fd,:h,:p,:lo,:hi,:ver,:fish,:loc)
                ON CONFLICT (forecast_date, horizon, fish, location) DO UPDATE
                SET blended_prediction=EXCLUDED.blended_prediction, conf_lower=EXCLUDED.conf_lower,
                    conf_upper=EXCLUDED.conf_upper, model_version=EXCLUDED.model_version, generated_at=NOW()
            """), {"fd": target, "h": h, "p": blended, "lo": lo, "hi": hi,
                   "ver": model_version, "fish": FISH, "loc": LOCATION})

    print("\n✅ Ensemble forecasts saved to database.")


if __name__ == "__main__":
    main()
