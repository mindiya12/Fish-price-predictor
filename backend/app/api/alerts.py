from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from app.db.session import engine
from typing import List

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

class AlertCreate(BaseModel):
    email: EmailStr
    target_price: float
    fish: str = "balaya"
    location: str = "peliyagoda"

class AlertOut(AlertCreate):
    id: int
    is_active: bool

@router.post("/", response_model=AlertOut)
def create_alert(alert: AlertCreate):
    query = text("""
        INSERT INTO price_alerts (email, target_price, fish, location)
        VALUES (:email, :target_price, :fish, :location)
        RETURNING id, email, target_price, fish, location, is_active
    """)
    with engine.begin() as conn:
        res = conn.execute(query, {
            "email": alert.email,
            "target_price": alert.target_price,
            "fish": alert.fish,
            "location": alert.location
        }).fetchone()
        
    return AlertOut(
        id=res.id,
        email=res.email,
        target_price=float(res.target_price),
        fish=res.fish,
        location=res.location,
        is_active=res.is_active
    )

@router.get("/{email}", response_model=List[AlertOut])
def get_user_alerts(email: str):
    query = text("""
        SELECT id, email, target_price, fish, location, is_active
        FROM price_alerts
        WHERE email = :email
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"email": email}).fetchall()
    
    return [
        AlertOut(
            id=r.id,
            email=r.email,
            target_price=float(r.target_price),
            fish=r.fish,
            location=r.location,
            is_active=r.is_active
        ) for r in rows
    ]

@router.delete("/{alert_id}")
def delete_alert(alert_id: int):
    query = text("DELETE FROM price_alerts WHERE id = :id")
    with engine.begin() as conn:
        conn.execute(query, {"id": alert_id})
    return {"status": "deleted"}
