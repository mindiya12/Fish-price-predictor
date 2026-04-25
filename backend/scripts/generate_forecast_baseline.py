import os
from datetime import date
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
FISH = os.environ.get("FISH", "balaya")
LOCATION = os.environ.get("LOCATION", "peliyagoda")

def main():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT date, price
            FROM price_history
            WHERE fish = :fish AND location = :location
            ORDER BY date DESC
            LIMIT 7
        """), {"fish": FISH, "location": LOCATION}).fetchall()

        if len(rows) < 7:
            raise RuntimeError("Need at least 7 days of history to compute MA7 baseline")

        last7 = [float(r[1]) for r in rows]
        ma7 = sum(last7) / 7.0

        # use latest history date as "base", insert forecast_date = base_date
        base_date = rows[0][0]
        forecast_date = base_date

        # simple confidence band (placeholder for now)
        conf = 50.0
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

        for h in range(1, 4):
            conn.execute(insert_q, {
                "forecast_date": forecast_date,
                "horizon": h,
                "pred": ma7,
                "lo": ma7 - conf,
                "hi": ma7 + conf,
                "location": LOCATION,
                "fish": FISH,
                "model_version": "baseline_ma7",
            })

    print("Inserted/updated 3-day baseline forecast.")

if __name__ == "__main__":
    main()
