import io
import pandas as pd
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter()

@router.get("/api/download/history")
def download_history(
    from_date: str = Query(..., alias="from"),
    to_date: str = Query(..., alias="to"),
    format: str = "csv",
    fish: str = "balaya",
    location: str = "peliyagoda",
    db: Session = Depends(get_db),
):
    q = text("""
        SELECT date, price, location, fish
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

    df = pd.DataFrame(rows, columns=["date", "price", "location", "fish"])

    if format.lower() == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=history.csv"},
        )

    if format.lower() in ("excel", "xlsx"):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="history")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=history.xlsx"},
        )

    raise HTTPException(status_code=400, detail="format must be csv or excel")
