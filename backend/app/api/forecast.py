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
    # In the current DB schema, `forecast_date` is the exact TARGET day of the prediction.
    # To get the latest 3-day forecast, we just fetch the most recent 3 distinct dates.
    # We order by generated_at DESC to ensure we get the latest run, then pull the 3 horizons.

    q = text("""
        SELECT forecast_date, horizon, blended_prediction, conf_lower, conf_upper
        FROM forecasts
        WHERE fish = :fish AND location = :location
        ORDER BY generated_at DESC, horizon ASC
        LIMIT 3
    """)
    rows = db.execute(q, {
        "fish": fish,
        "location": location,
    }).fetchall()
    
    # Sort them chronically by target date to ensure ascending order
    rows = sorted(rows, key=lambda x: x.forecast_date)

    if not rows:
        return {
            "forecastDate": None,
            "dates": [],
            "blended": [],
            "confidence": [],
            "confidenceLower": [],
            "confidenceUpper": [],
        }

    # latest run date is roughly 'generated_at' of the first row, but frontend just wants an ISO string.
    # We will just pass today as the "forecast run date".
    from datetime import date
    today_iso = date.today().isoformat()

    dates = []
    blended = []
    conf = []
    lower = []
    upper = []

    for r in rows:
        target_date, horizon, pred, lo, hi = r
        dates.append(target_date.isoformat())

        blended.append(float(pred))
        lower.append(float(lo) if lo is not None else None)
        upper.append(float(hi) if hi is not None else None)

        if lo is not None and hi is not None:
            conf.append(float(hi) - float(lo))
        else:
            # Default confidence band if not found
            conf.append(30.0)

    return {
        "forecastDate": today_iso,
        "dates": dates,
        "blended": blended,
        "confidence": conf,
        "confidenceLower": lower,
        "confidenceUpper": upper,
    }
