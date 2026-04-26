CREATE TABLE IF NOT EXISTS price_history (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  price NUMERIC NOT NULL,
  location TEXT NOT NULL DEFAULT 'peliyagoda',
  fish TEXT NOT NULL DEFAULT 'balaya',
  source TEXT NOT NULL DEFAULT 'seed',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(date, location, fish)
);

CREATE TABLE IF NOT EXISTS weather_data (
  id           SERIAL PRIMARY KEY,
  date         DATE NOT NULL,
  city         TEXT NOT NULL,
  temp_mean_c  NUMERIC,
  wind_max_kmh NUMERIC,
  gust_max_kmh NUMERIC,
  precip_mm    NUMERIC,
  created_at   TIMESTAMP DEFAULT NOW(),
  UNIQUE (date, city)
);
CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date);

CREATE TABLE IF NOT EXISTS fuel_prices (
  id         SERIAL PRIMARY KEY,
  date       DATE NOT NULL UNIQUE,
  lp_95      NUMERIC,
  lp_92      NUMERIC,
  lad        NUMERIC,
  lsd        NUMERIC,
  lk         NUMERIC,
  source     TEXT DEFAULT 'ceypetco',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inflation_data (
  id              SERIAL PRIMARY KEY,
  reference_month DATE NOT NULL UNIQUE,
  ccpi_headline   NUMERIC,
  ccpi_food       NUMERIC,
  ccpi_non_food   NUMERIC,
  source_pdf      TEXT,
  created_at      TIMESTAMP DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS forecasts (
  id SERIAL PRIMARY KEY,
  forecast_date DATE NOT NULL,
  horizon INT NOT NULL,
  blended_prediction NUMERIC NOT NULL,
  conf_lower NUMERIC,
  conf_upper NUMERIC,
  location TEXT NOT NULL DEFAULT 'peliyagoda',
  fish TEXT NOT NULL DEFAULT 'balaya',
  model_version TEXT DEFAULT 'baseline',
  generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(forecast_date, horizon, location, fish)
);

-- Stores validated past forecast accuracy: actual vs predicted
CREATE TABLE IF NOT EXISTS predictions (
  id SERIAL PRIMARY KEY,
  forecast_date DATE NOT NULL,
  horizon INT NOT NULL,
  predicted_price NUMERIC NOT NULL,
  actual_price NUMERIC,
  error NUMERIC GENERATED ALWAYS AS (actual_price - predicted_price) STORED,
  abs_error NUMERIC GENERATED ALWAYS AS (ABS(actual_price - predicted_price)) STORED,
  pct_error NUMERIC GENERATED ALWAYS AS (
    CASE WHEN actual_price IS NOT NULL AND actual_price <> 0
         THEN ABS((actual_price - predicted_price) / actual_price) * 100
    END
  ) STORED,
  fish TEXT NOT NULL DEFAULT 'balaya',
  location TEXT NOT NULL DEFAULT 'peliyagoda',
  model_version TEXT DEFAULT 'baseline',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(forecast_date, horizon, fish, location)
);

-- Stores per-horizon model performance metrics after each training run
CREATE TABLE IF NOT EXISTS model_metrics (
  id SERIAL PRIMARY KEY,
  model_version TEXT NOT NULL,
  horizon INT NOT NULL,
  rmse NUMERIC,
  mae NUMERIC,
  mape NUMERIC,
  r2_score NUMERIC,
  xgb_weight NUMERIC DEFAULT 0.7,
  fish TEXT NOT NULL DEFAULT 'balaya',
  location TEXT NOT NULL DEFAULT 'peliyagoda',
  is_production BOOLEAN NOT NULL DEFAULT FALSE,
  trained_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(model_version, horizon, fish, location)
);

-- Safe upgrades for existing deployments
ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS r2_score NUMERIC;
ALTER TABLE model_metrics ADD COLUMN IF NOT EXISTS xgb_weight NUMERIC DEFAULT 0.7;

-- Stores per-feature importance values from each training run
CREATE TABLE IF NOT EXISTS feature_importance (
  id SERIAL PRIMARY KEY,
  model_version TEXT NOT NULL,
  horizon INT NOT NULL,
  feature_name TEXT NOT NULL,
  importance_score NUMERIC NOT NULL,
  fish TEXT NOT NULL DEFAULT 'balaya',
  location TEXT NOT NULL DEFAULT 'peliyagoda',
  trained_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(model_version, horizon, feature_name, fish, location)
);

-- Catalog of fish species and their availability status
CREATE TABLE IF NOT EXISTS fish_types (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  name_sinhala TEXT,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  location TEXT NOT NULL DEFAULT 'peliyagoda',
  available_from TEXT DEFAULT NULL  -- e.g. 'Q2 2025' for coming-soon messaging
);

-- Seed fish_types (run only if empty)
INSERT INTO fish_types (name, name_sinhala, active, location, available_from)
VALUES
  ('balaya',    'බලයා',    TRUE,  'peliyagoda', NULL),
  ('kelawalla', 'කෙලවල්ල', FALSE, 'peliyagoda', 'Q3 2026'),
  ('thalapath', 'තලපත්',   FALSE, 'peliyagoda', 'Q3 2026'),
  ('salaya',    'සාලයා',   FALSE, 'peliyagoda', 'Q3 2026'),
  ('hurulla',   'හුරුල්ල',  FALSE, 'peliyagoda', 'Q3 2026'),
  ('paraw',     'පාරාව',   FALSE, 'peliyagoda', 'Q3 2026')
ON CONFLICT (name) DO NOTHING;

-- User-defined price threshold alerts
CREATE TABLE IF NOT EXISTS price_alerts (
  id SERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  target_price NUMERIC NOT NULL,
  fish TEXT NOT NULL DEFAULT 'balaya',
  location TEXT NOT NULL DEFAULT 'peliyagoda',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
