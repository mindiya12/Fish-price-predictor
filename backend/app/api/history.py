from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter()

@router.get("/api/history")
def get_history(
    from_date: str = Query(..., alias="from"),
    to_date: str = Query(..., alias="to"),
    fish: str = "balaya",
    location: str = "peliyagoda",
    db: Session = Depends(get_db),
):
    q = text("""
        SELECT date, price
        FROM price_history
        WHERE date BETWEEN :from_date AND :to_date
          AND fish = :fish
          AND location = :location
        ORDER BY date ASC
    """)
    rows = db.execute(q, {
        "from_date": from_date,
        "to_date": to_date,
        "fish": fish,
        "location": location,
    }).fetchall()

    return {
        "dates": [r[0].isoformat() for r in rows],
        "prices": [float(r[1]) for r in rows],
    }
