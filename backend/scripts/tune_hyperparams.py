"""
Hyperparameter Tuning - Bayesian Optimization with Optuna
===========================================================
Uses Optuna to efficiently search the hyperparameter space.
Optimizes for lowest MAE across TimeSeriesSplit CV.
"""

import os
import sys
import joblib
import warnings
import pandas as pd
import numpy as np
from datetime import date
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sqlalchemy import create_engine, text

try:
    import optuna
    from optuna.samplers import TPESampler
except ImportError:
    print("❌ Optuna not installed. Install with: pip install optuna")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poya_days import POYA_DATES, days_until_next_poya, days_since_last_poya

warnings.filterwarnings("ignore")

DATABASE_URL = os.environ.get("DATABASE_URL")
FISH         = os.environ.get("FISH", "balaya")
LOCATION     = os.environ.get("LOCATION", "peliyagoda")
MODELS_DIR   = os.environ.get("MODELS_DIR", "/app/models")
N_TRIALS     = int(os.environ.get("N_TRIALS", "100"))
CV_SPLITS    = int(os.environ.get("CV_SPLITS", "5"))

TARGET_COL      = "price"
COLS_TO_EXCLUDE = ["date", "season", TARGET_COL]


def load_training_data(engine) -> pd.DataFrame:
    """Load training data with all engineered features (same as train_models_xgb.py)"""
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

    for col in ["Inflation_Rate", "CCPI_Food"]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            s = s.where((s >= -100) & (s <= 100), np.nan)
            df[col] = s.ffill().bfill().fillna(0.0)

    # Calendar features
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek
    df["quarter"] = df["date"].dt.quarter
    df["day_of_year"] = df["date"].dt.dayofyear
    df["day_of_month"] = df["date"].dt.day
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    
    df["sin_month"] = np.sin(2*np.pi*df["month"]/12)
    df["cos_month"] = np.cos(2*np.pi*df["month"]/12)
    df["sin_day_year"] = np.sin(2*np.pi*df["day_of_year"]/365)
    df["cos_day_year"] = np.cos(2*np.pi*df["day_of_year"]/365)
    df["sin_week"] = np.sin(2*np.pi*df["week_of_year"]/52)
    df["cos_week"] = np.cos(2*np.pi*df["week_of_year"]/52)

    # Poya features
    date_col = df["date"].dt.date
    df["is_poya"] = date_col.isin(POYA_DATES).astype(int)
    df["days_until_next_poya"] = date_col.apply(days_until_next_poya)
    df["days_since_last_poya"] = date_col.apply(days_since_last_poya)
    df["is_pre_poya"] = df["days_until_next_poya"].isin([1,2]).astype(int)
    df["is_post_poya"] = df["days_since_last_poya"].isin([1,2]).astype(int)

    # Extended lags
    for lag in [1,2,3,5,7,14,21,30]:
        df[f"price_lag{lag}"] = df["price"].shift(lag)

    # Rolling stats
    p = df["price"].shift(1)
    for w in [3,7,14,30]:
        df[f"price_roll_mean_{w}"] = p.rolling(w).mean()
        df[f"price_roll_std_{w}"] = p.rolling(w).std()
        df[f"price_roll_min_{w}"] = p.rolling(w).min()
        df[f"price_roll_max_{w}"] = p.rolling(w).max()
        df[f"price_roll_range_{w}"] = df[f"price_roll_max_{w}"] - df[f"price_roll_min_{w}"]

    # EWM
    df["price_ewm7"] = p.ewm(span=7, adjust=False).mean()
    df["price_ewm14"] = p.ewm(span=14, adjust=False).mean()
    df["price_ewm30"] = p.ewm(span=30, adjust=False).mean()

    # Momentum
    df["price_change"] = df["price"] - df["price_lag1"]
    df["price_change_1d"] = df["price_change"]
    df["price_change_7d"] = df["price"] - df["price_lag7"]
    df["price_change_14d"] = df["price"] - df["price_lag14"]
    df["price_pct_change_1d"] = df["price"].pct_change(1)
    df["price_pct_change_7d"] = df["price"].pct_change(7)
    df["price_acceleration"] = df["price_change_1d"] - df["price_change_1d"].shift(1)
    df["price_dev_from_7d"] = df["price_lag1"] - df["price_roll_mean_7"]
    df["price_dev_from_30d"] = df["price_lag1"] - df["price_roll_mean_30"]
    df["price_trend_ratio_7_30"] = df["price_roll_mean_7"] / (df["price_roll_mean_30"] + 1e-9)
    df["price_volatility_7d"] = p.rolling(7).std()
    df["price_volatility_30d"] = p.rolling(30).std()

    # Exogenous change features
    exog_shift = 1
    for col in ["LP 95", "LP 92", "LAD", "LSD", "LK"]:
        if col in df.columns:
            s = df[col].shift(exog_shift)
            df[f"{col}_chg_1d"] = s.diff(1)
            df[f"{col}_chg_7d"] = s.diff(7)

    for col in ["Inflation_Rate", "CCPI_Food"]:
        if col in df.columns:
            s = df[col].shift(exog_shift)
            df[f"{col}_chg_30d"] = s.diff(30)

    for col in ["avg_temp_mean_C", "avg_wind_max_kmh", "avg_gust_max_kmh", "avg_precip_mm"]:
        if col in df.columns:
            s = df[col].shift(exog_shift)
            df[f"{col}_lag1"] = s.shift(0)
            df[f"{col}_roll_mean_3"] = s.rolling(3).mean()
            df[f"{col}_roll_mean_7"] = s.rolling(7).mean()
            if "precip" in col:
                df[f"{col}_roll_sum_3"] = s.rolling(3).sum()
                df[f"{col}_roll_sum_7"] = s.rolling(7).sum()

    # Regime
    d1 = df["price_change_1d"].shift(1)
    df["delta_roll_std_7"] = d1.rolling(7).std()
    df["delta_roll_std_30"] = d1.rolling(30).std()
    df["shock_1d"] = (d1.abs() > (1.5 * (df["delta_roll_std_30"] + 1e-9))).astype(int)

    # ── ENHANCED FEATURES (Phase 2.5) ──────────────────────────────────────
    df["price_change_squared"] = df["price_change_1d"] ** 2
    df["price_change_abs"] = np.abs(df["price_change_1d"])
    df["price_change_sign_switch"] = (df["price_change_1d"] * df["price_change_1d"].shift(1) < 0).astype(int)
    
    vol_30 = df["price_volatility_30d"]
    df["adaptive_momentum_1d"] = df["price_change_1d"] / (vol_30 + 1e-9)
    df["adaptive_momentum_7d"] = df["price_change_7d"] / (vol_30 + 1e-9)
    df["price_momentum_ratio"] = (df["price_change_7d"] + 1e-9) / (df["price_change_1d"].abs() + 1e-9)
    
    df["price_acceleration_abs"] = np.abs(df["price_acceleration"])
    df["price_accel_signed"] = df["price_acceleration"]
    df["acceleration_momentum"] = df["price_acceleration"] * df["price_change_1d"]
    
    df["price_drawdown_7d"] = (df["price_roll_max_7"] - df["price_lag1"]) / (df["price_roll_range_7"] + 1e-9)
    df["price_drawup_7d"] = (df["price_lag1"] - df["price_roll_min_7"]) / (df["price_roll_range_7"] + 1e-9)
    df["price_drawdown_30d"] = (df["price_roll_max_30"] - df["price_lag1"]) / (df["price_roll_range_30"] + 1e-9)
    df["price_drawup_30d"] = (df["price_lag1"] - df["price_roll_min_30"]) / (df["price_roll_range_30"] + 1e-9)
    
    vol_7_p75 = df["price_volatility_7d"].quantile(0.75)
    vol_7_p90 = df["price_volatility_7d"].quantile(0.90)
    df["high_volatility_flag"] = (df["price_volatility_7d"] > vol_7_p75).astype(int)
    df["extreme_volatility_flag"] = (df["price_volatility_7d"] > vol_7_p90).astype(int)
    df["vol_increasing"] = (df["price_volatility_7d"] > df["price_volatility_7d"].shift(7)).astype(int)
    
    shock_series = d1.abs() > (1.5 * (df["delta_roll_std_30"] + 1e-9))
    shock_groups = (shock_series != shock_series.shift()).cumsum()
    df["shock_duration"] = shock_series.groupby(shock_groups).cumsum()
    df["shock_duration"] = df["shock_duration"] * shock_series
    df["days_since_shock"] = (~shock_series).groupby((~shock_series) != (~shock_series).shift()).cumsum()
    df["days_since_shock"] = df["days_since_shock"] * (~shock_series)
    
    df["price_lag1_x_sin_month"] = df["price_lag1"] * df["sin_month"]
    df["price_lag1_x_cos_month"] = df["price_lag1"] * df["cos_month"]
    df["price_lag1_x_is_poya"] = df["price_lag1"] * df["is_poya"]
    df["price_lag1_x_is_pre_poya"] = df["price_lag1"] * df["is_pre_poya"]
    df["change_x_day_of_week"] = df["price_change_1d"] * (df["day_of_week"] - 2.5)
    
    if "LP 95" in df.columns and "LP 92" in df.columns:
        lp95_pct_change = df["LP 95"].pct_change(1).fillna(0)
        df["volatility_x_fuel_change"] = df["price_volatility_7d"] * lp95_pct_change
    
    if "Inflation_Rate" in df.columns:
        df["volatility_x_inflation"] = df["price_volatility_7d"] * (df["Inflation_Rate"] / 100.0 + 1e-9)
    
    if "avg_precip_mm" in df.columns:
        df["precip_x_momentum"] = df["avg_precip_mm"] * df["price_change_1d"]
    
    df["velocity_of_change"] = df["price_change_1d"] - df["price_change_1d"].shift(1)
    df["consecutive_up_days"] = ((df["price_change_1d"] > 0).astype(int) * 
                                  ((df["price_change_1d"] > 0) == (df["price_change_1d"].shift(1) > 0)).astype(int)).rolling(7).sum()
    df["consecutive_down_days"] = ((df["price_change_1d"] < 0).astype(int) * 
                                   ((df["price_change_1d"] < 0) == (df["price_change_1d"].shift(1) < 0)).astype(int)).rolling(7).sum()
    
    df["price_lag1_weighted_vol"] = df["price_lag1"] * df["price_volatility_7d"]
    df["price_lag7_weighted_vol"] = df["price_lag7"] * df["price_volatility_7d"]
    
    df["momentum_ewm7"] = df["price_change_1d"].ewm(span=7, adjust=False).mean()
    df["momentum_ewm14"] = df["price_change_1d"].ewm(span=14, adjust=False).mean()
    
    if "LP 95_chg_1d" in df.columns and "avg_precip_mm_lag1" in df.columns:
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
    # Same as train_models_xgb.py
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
        'LP 95_chg_1d','LP 95_chg_7d','LP 92_chg_1d','LP 92_chg_7d','LAD_chg_1d','LAD_chg_7d','LSD_chg_1d','LSD_chg_7d','LK_chg_1d','LK_chg_7d',
        'Inflation_Rate_chg_30d','CCPI_Food_chg_30d',
        'avg_temp_mean_C_lag1','avg_temp_mean_C_roll_mean_3','avg_temp_mean_C_roll_mean_7',
        'avg_wind_max_kmh_lag1','avg_wind_max_kmh_roll_mean_3','avg_wind_max_kmh_roll_mean_7',
        'avg_gust_max_kmh_lag1','avg_gust_max_kmh_roll_mean_3','avg_gust_max_kmh_roll_mean_7',
        'avg_precip_mm_lag1','avg_precip_mm_roll_mean_3','avg_precip_mm_roll_mean_7','avg_precip_mm_roll_sum_3','avg_precip_mm_roll_sum_7',
        'delta_roll_std_7','delta_roll_std_30','shock_1d',
        'price_change_squared','price_change_abs','price_change_sign_switch',
        'adaptive_momentum_1d','adaptive_momentum_7d','price_momentum_ratio',
        'price_acceleration_abs','price_accel_signed','acceleration_momentum',
        'price_drawdown_7d','price_drawup_7d','price_drawdown_30d','price_drawup_30d',
        'high_volatility_flag','extreme_volatility_flag','vol_increasing',
        'shock_duration','days_since_shock',
        'price_lag1_x_sin_month','price_lag1_x_cos_month','price_lag1_x_is_poya','price_lag1_x_is_pre_poya',
        'change_x_day_of_week',
        'volatility_x_fuel_change','volatility_x_inflation','precip_x_momentum',
        'velocity_of_change','consecutive_up_days','consecutive_down_days',
        'price_lag1_weighted_vol','price_lag7_weighted_vol',
        'momentum_ewm7','momentum_ewm14',
        'expected_change_macro','unexpected_change',
    ]
    available = [c for c in core if c in df.columns]
    extra = [c for c in df.columns if c not in COLS_TO_EXCLUDE + ["date","ym"] and c not in available]
    return available + extra


def evaluate_params(xgb_params, lgbm_params, X, y, n_splits=5):
    """Cross-validation evaluation of parameters"""
    tscv = TimeSeriesSplit(n_splits=n_splits, gap=3)
    maes = []
    
    for tr_idx, val_idx in tscv.split(X):
        X_tr, X_val = X.iloc[tr_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[tr_idx], y.iloc[val_idx]
        
        val_size = max(10, int(len(X_tr) * 0.1))
        X_tr2, X_es = X_tr.iloc[:-val_size], X_tr.iloc[-val_size:]
        y_tr2, y_es = y_tr.iloc[:-val_size], y_tr.iloc[-val_size:]
        
        # Train XGBoost
        xgb_model = XGBRegressor(**xgb_params)
        xgb_model.fit(X_tr2, y_tr2, eval_set=[(X_es, y_es)], verbose=False)
        xgb_pred = xgb_model.predict(X_val)
        
        # Train LightGBM
        lgbm_model = LGBMRegressor(**lgbm_params)
        lgbm_model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], callbacks=[], verbose=-1)
        lgbm_pred = lgbm_model.predict(X_val)
        
        # Ensemble: 45% XGB + 45% LGBM
        ensemble_pred = 0.45 * xgb_pred + 0.45 * lgbm_pred + 0.10 * y_val.mean()
        mae = mean_absolute_error(y_val, ensemble_pred)
        maes.append(mae)
    
    return float(np.mean(maes))


def objective_xgb(trial, X_train_full, y_train_full):
    """Optuna objective for XGBoost hyperparameters"""
    xgb_params = {
        "n_estimators": 2000,
        "max_depth": trial.suggest_int("xgb_max_depth", 4, 8),
        "learning_rate": trial.suggest_float("xgb_lr", 0.005, 0.05, log=True),
        "subsample": trial.suggest_float("xgb_subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("xgb_colsample", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("xgb_mcw", 1, 10),
        "reg_alpha": trial.suggest_float("xgb_alpha", 0.0, 0.5, log=True),
        "reg_lambda": trial.suggest_float("xgb_lambda", 0.5, 5.0, log=True),
        "random_state": 42,
        "n_jobs": -1,
        "early_stopping_rounds": 50,
        "objective": "reg:pseudohubererror",
        "eval_metric": "rmse",
    }
    
    lgbm_params = {
        "n_estimators": 2000,
        "max_depth": 6,
        "learning_rate": 0.02,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_samples": 20,
        "reg_alpha": 0.01,
        "reg_lambda": 2.0,
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1,
        "objective": "huber",
    }
    
    mae = evaluate_params(xgb_params, lgbm_params, X_train_full, y_train_full, n_splits=CV_SPLITS)
    return mae


def objective_lgbm(trial, X_train_full, y_train_full):
    """Optuna objective for LightGBM hyperparameters"""
    xgb_params = {
        "n_estimators": 2000,
        "max_depth": 6,
        "learning_rate": 0.02,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "reg_alpha": 0.01,
        "reg_lambda": 2.0,
        "random_state": 42,
        "n_jobs": -1,
        "early_stopping_rounds": 50,
        "objective": "reg:pseudohubererror",
        "eval_metric": "rmse",
    }
    
    lgbm_params = {
        "n_estimators": 2000,
        "max_depth": trial.suggest_int("lgbm_max_depth", 4, 8),
        "learning_rate": trial.suggest_float("lgbm_lr", 0.005, 0.05, log=True),
        "subsample": trial.suggest_float("lgbm_subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("lgbm_colsample", 0.6, 1.0),
        "min_child_samples": trial.suggest_int("lgbm_mcs", 10, 50),
        "reg_alpha": trial.suggest_float("lgbm_alpha", 0.0, 0.5, log=True),
        "reg_lambda": trial.suggest_float("lgbm_lambda", 0.5, 5.0, log=True),
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1,
        "objective": "huber",
    }
    
    mae = evaluate_params(xgb_params, lgbm_params, X_train_full, y_train_full, n_splits=CV_SPLITS)
    return mae


def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(DATABASE_URL)
    df = load_training_data(engine)
    feature_cols = get_feature_cols(df)
    
    print(f"\n{'='*60}")
    print(f"  HYPERPARAMETER TUNING - Bayesian Optimization")
    print(f"{'='*60}")
    print(f"N_TRIALS: {N_TRIALS} | CV_SPLITS: {CV_SPLITS}")
    print(f"Features: {len(feature_cols)}")
    
    test_size = 30
    train_df = df.iloc[:-test_size].copy()
    train_df = clean_data(train_df, feature_cols)
    
    print(f"\n📊 Training Data: {len(train_df)} rows")
    print(f"\n{'='*60}")
    
    # ── Tune XGBoost ──────────────────────────────────────────────────────────
    print(f"\n🔍 Tuning XGBoost parameters...")
    y_train = (train_df[TARGET_COL].shift(-1) - train_df[TARGET_COL]).dropna()
    X_train = train_df[feature_cols].iloc[:len(y_train)]
    
    sampler_xgb = TPESampler(seed=42, n_startup_trials=10)
    study_xgb = optuna.create_study(sampler=sampler_xgb, direction='minimize')
    study_xgb.optimize(
        lambda trial: objective_xgb(trial, X_train, y_train),
        n_trials=N_TRIALS // 2,
        show_progress_bar=True
    )
    
    best_xgb_params = study_xgb.best_params
    best_xgb_mae = study_xgb.best_value
    print(f"\n✅ XGBoost Best MAE: {best_xgb_mae:.4f}")
    print(f"   Best params: {best_xgb_params}")
    
    # ── Tune LightGBM ─────────────────────────────────────────────────────────
    print(f"\n🔍 Tuning LightGBM parameters...")
    sampler_lgbm = TPESampler(seed=42, n_startup_trials=10)
    study_lgbm = optuna.create_study(sampler=sampler_lgbm, direction='minimize')
    study_lgbm.optimize(
        lambda trial: objective_lgbm(trial, X_train, y_train),
        n_trials=N_TRIALS // 2,
        show_progress_bar=True
    )
    
    best_lgbm_params = study_lgbm.best_params
    best_lgbm_mae = study_lgbm.best_value
    print(f"\n✅ LightGBM Best MAE: {best_lgbm_mae:.4f}")
    print(f"   Best params: {best_lgbm_params}")
    
    # ── Save results ──────────────────────────────────────────────────────────
    results = {
        "xgb_best_params": best_xgb_params,
        "xgb_best_mae": best_xgb_mae,
        "lgbm_best_params": best_lgbm_params,
        "lgbm_best_mae": best_lgbm_mae,
        "baseline_mae_xgb": 63,  # Current MAE from previous training
    }
    
    results_path = os.path.join(MODELS_DIR, "hyperparams_results.pkl")
    joblib.dump(results, results_path)
    print(f"\n💾 Results saved to {results_path}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"{'='*60}")
    print(f"Previous MAE: 63")
    print(f"XGBoost Tuned MAE: {best_xgb_mae:.4f}")
    print(f"LightGBM Tuned MAE: {best_lgbm_mae:.4f}")
    print(f"Expected improvement: {((63 - min(best_xgb_mae, best_lgbm_mae)) / 63 * 100):.1f}%")
    print(f"\n📝 Copy best params into train_models_xgb.py XGB_PARAMS and LGBM_PARAMS")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
