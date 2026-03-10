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
