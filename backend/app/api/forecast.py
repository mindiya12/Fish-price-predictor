from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter()

@router.get("/api/forecast/latest")
def get_latest_forecast(
    fish: str = "balaya",
    location: str = "peliyagoda",
    db: Session = Depends(get_db),
):
    # latest forecast_date for this fish/location
    latest_date_q = text("""
        SELECT MAX(forecast_date)
        FROM forecasts
        WHERE fish = :fish AND location = :location
    """)
    latest_date = db.execute(latest_date_q, {"fish": fish, "location": location}).scalar()

    if latest_date is None:
        return {
            "forecastDate": None,
            "dates": [],
            "blended": [],
            "confidence": [],
            "confidenceLower": [],
            "confidenceUpper": [],
        }

    q = text("""
        SELECT forecast_date, horizon, blended_prediction, conf_lower, conf_upper
        FROM forecasts
        WHERE forecast_date = :forecast_date
          AND fish = :fish
          AND location = :location
        ORDER BY horizon ASC
    """)
    rows = db.execute(q, {
        "forecast_date": latest_date,
        "fish": fish,
        "location": location,
    }).fetchall()

    # frontend likes a per-day list; horizons are 1..7
    dates = []
    blended = []
    conf = []
    lower = []
    upper = []

    for r in rows:
        forecast_date, horizon, pred, lo, hi = r
        day = forecast_date.toordinal() + int(horizon)
        # Convert ordinal back to ISO date string
        # (simple and avoids timezone issues)
        from datetime import date
        dates.append(date.fromordinal(day).isoformat())

        blended.append(float(pred))
        lower.append(float(lo) if lo is not None else None)
        upper.append(float(hi) if hi is not None else None)

        if lo is not None and hi is not None:
            conf.append(float(hi) - float(lo))
        else:
            conf.append(None)

    return {
        "forecastDate": latest_date.isoformat(),
        "dates": dates,
        "blended": blended,
        "confidence": conf,
        "confidenceLower": lower,
        "confidenceUpper": upper,
    }
