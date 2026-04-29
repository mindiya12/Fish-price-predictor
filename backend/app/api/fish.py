from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter()


@router.get("/api/forecast/{horizon}")
def get_forecast_by_horizon(
    horizon: int,
    fish: str = "balaya",
    location: str = "peliyagoda",
    db: Session = Depends(get_db),
):
    """Return the latest forecast for a specific horizon (1-7)."""
    if horizon < 1 or horizon > 7:
        raise HTTPException(status_code=400, detail="horizon must be between 1 and 7")

    # Find the most recent forecast date
    latest_date = db.execute(
        text("""
            SELECT MAX(forecast_date) FROM forecasts
            WHERE fish = :fish AND location = :location
        """),
        {"fish": fish, "location": location},
    ).scalar()

    if latest_date is None:
        raise HTTPException(status_code=404, detail="No forecast found")

    row = db.execute(
        text("""
            SELECT forecast_date, horizon, blended_prediction, conf_lower, conf_upper, model_version
            FROM forecasts
            WHERE forecast_date = :forecast_date
              AND horizon = :horizon
              AND fish = :fish
              AND location = :location
        """),
        {
            "forecast_date": latest_date,
            "horizon": horizon,
            "fish": fish,
            "location": location,
        },
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"No forecast found for horizon {horizon}")

    from datetime import date
    forecast_date, h, pred, lo, hi, model_version = row
    target_date = date.fromordinal(forecast_date.toordinal() + int(h))

    conf = (float(hi) - float(lo)) if (lo is not None and hi is not None) else None

    return {
        "forecastDate": forecast_date.isoformat(),
        "targetDate": target_date.isoformat(),
        "horizon": h,
        "price": float(pred),
        "confLower": float(lo) if lo is not None else None,
        "confUpper": float(hi) if hi is not None else None,
        "confidence": conf,
        "modelVersion": model_version,
        "fish": fish,
        "location": location,
    }


@router.get("/api/fish-types")
def get_fish_types(
    location: str = "peliyagoda",
    db: Session = Depends(get_db),
):
    """Return all fish species and their active/coming-soon status."""
    rows = db.execute(
        text("""
            SELECT name, name_sinhala, active, location, available_from
            FROM fish_types
            WHERE location = :location
            ORDER BY active DESC, name ASC
        """),
        {"location": location},
    ).fetchall()

    return [
        {
            "name": r[0],
            "nameSinhala": r[1],
            "active": r[2],
            "location": r[3],
            "availableFrom": r[4],
        }
        for r in rows
    ]


@router.get("/api/today-price")
def get_today_price(
    fish: str = "balaya",
    location: str = "peliyagoda",
    db: Session = Depends(get_db),
):
    """Return today's actual price if available, otherwise the forecast for today."""
    from datetime import date

    today = date.today().isoformat()

    # Try to get today's actual price from history
    actual_price = db.execute(
        text("""
            SELECT price
            FROM price_history
            WHERE date = :date
              AND fish = :fish
              AND location = :location
        """),
        {"date": today, "fish": fish, "location": location},
    ).scalar()

    if actual_price is not None:
        return {
            "date": today,
            "price": float(actual_price),
            "type": "actual",
            "fish": fish,
            "location": location,
        }

    # If no actual price, get today's forecast (horizon 1)
    today_forecast = db.execute(
        text("""
            SELECT blended_prediction, conf_lower, conf_upper
            FROM forecasts
            WHERE forecast_date = :forecast_date
              AND horizon = 1
              AND fish = :fish
              AND location = :location
            ORDER BY generated_at DESC
            LIMIT 1
        """),
        {"forecast_date": today, "fish": fish, "location": location},
    ).fetchone()

    if today_forecast:
        pred, lo, hi = today_forecast
        return {
            "date": today,
            "price": float(pred),
            "confLower": float(lo) if lo is not None else None,
            "confUpper": float(hi) if hi is not None else None,
            "type": "forecast",
            "fish": fish,
            "location": location,
        }

    return {
        "date": today,
        "price": None,
        "type": None,
        "fish": fish,
        "location": location,
    }
