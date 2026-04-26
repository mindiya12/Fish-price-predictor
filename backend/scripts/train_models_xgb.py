"""
Train Models - Phase 2: Ensemble (XGBoost + LightGBM) + Early Stopping + CV
=============================================================================
Phase 2 additions:
  - LightGBM trained per horizon alongside XGBoost
  - XGBoost early stopping (no more overfitting on 1500 trees)
  - TimeSeriesSplit (5-fold) CV for realistic out-of-sample evaluation
  - Blend updated: 40% XGB + 40% LGBM + 20% MA7
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

# Phase 2 blend: 40% XGB + 40% LGBM + 20% MA7
XGB_WEIGHT  = 0.40
LGBM_WEIGHT = 0.40
MA7_WEIGHT  = 0.20

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

    # Calendar
    df["year"]         = df["date"].dt.year
    df["month"]        = df["date"].dt.month
    df["day_of_week"]  = df["date"].dt.dayofweek
    df["is_weekend"]   = (df["day_of_week"] >= 5).astype(int)
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
    df["is_national_holiday"] = 0
    df["is_market_holiday"]   = df["is_weekend"]

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
        'year','month','day_of_week','is_weekend','day_of_year','quarter','day_of_month','week_of_year',
        'sin_month','cos_month','sin_day_year','cos_day_year','sin_week','cos_week',
        'is_national_holiday','is_market_holiday',
        'is_poya','days_until_next_poya','days_since_last_poya','is_pre_poya','is_post_poya',
        'Inflation_Rate','CCPI_Food','LP 95','LP 92','LAD','LSD','LK',
        'Galle_production','Kalutara_production','Matara_production','Negombo_production','Tangalla_production',
        'total_production','production_change','production_lag1','production_lag7',
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
    ]
    available = [c for c in core if c in df.columns]
    extra = [c for c in df.columns if c not in COLS_TO_EXCLUDE + ["date","ym"] and c not in available]
    return available + extra


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
    print(f"Blend: XGB×{XGB_WEIGHT}  LGBM×{LGBM_WEIGHT}  MA7×{MA7_WEIGHT}\n")

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

        y_train_full = train_df[TARGET_COL].shift(-h).dropna()
        X_train_full = train_df[feature_cols].iloc[:len(y_train_full)]
        y_test       = test_df[TARGET_COL].shift(-h).dropna()
        X_test       = test_df[feature_cols].iloc[:len(y_test)]

        # ── Phase 2: TimeSeriesSplit CV ───────────────────────────────────────
        print(f"\n  [CV] Running 5-fold TimeSeriesSplit...")
        cv_results = run_tscv(X_train_full, y_train_full, XGB_PARAMS, LGBM_PARAMS)
        print(f"\n  CV Summary:")
        print(f"    XGB  → CV RMSE={cv_results['xgb_cv_rmse']:.2f}  CV MAPE={cv_results['xgb_cv_mape']:.2f}%")
        print(f"    LGBM → CV RMSE={cv_results['lgbm_cv_rmse']:.2f}  CV MAPE={cv_results['lgbm_cv_mape']:.2f}%")

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
        if len(y_test) > 0:
            xgb_preds  = xgb_model.predict(X_test)
            lgbm_preds = lgbm_model.predict(X_test)
            # Ensemble on holdout
            ma7_val    = float(train_df["price"].tail(7).mean())
            ens_preds  = XGB_WEIGHT * xgb_preds + LGBM_WEIGHT * lgbm_preds + MA7_WEIGHT * ma7_val

            def metrics_row(name, preds):
                rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
                mae  = float(mean_absolute_error(y_test, preds))
                mape = float(mean_absolute_percentage_error(y_test, preds)*100)
                r2   = float(r2_score(y_test, preds))
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
    model_version = f"ensemble_p2_{pd.Timestamp.now().strftime('%Y%m%d')}"
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
    ma7 = float(df["price"].tail(7).mean())
    print(f"\nGenerating 3-day ensemble forecast (MA7={ma7:.0f}):")

    with engine.begin() as conn:
        for h in range(1, 4):
            xgb_pred  = float(xgb_models[h].predict(last_row[feature_cols])[0])
            lgbm_pred = float(lgbm_models[h].predict(last_row[feature_cols])[0])
            blended   = XGB_WEIGHT * xgb_pred + LGBM_WEIGHT * lgbm_pred + MA7_WEIGHT * ma7
            rmse_h    = next(m["rmse"] for m in metrics if m["horizon"] == h)
            lo, hi    = blended - rmse_h, blended + rmse_h
            target    = (df["date"].iloc[-1] + pd.Timedelta(days=h)).date()

            print(f"  h={h} ({target}): XGB={xgb_pred:.1f}  LGBM={lgbm_pred:.1f}  Ensemble={blended:.1f}  CI=[{lo:.0f},{hi:.0f}]")
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
