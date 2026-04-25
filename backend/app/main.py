from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from pathlib import Path
from app.api import history, forecast, download, fish, admin
from app.api.admin import run_daily_scrape
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(title="Fish Price API")

scheduler = BackgroundScheduler()

app.include_router(history.router)
app.include_router(forecast.router)
app.include_router(download.router)
app.include_router(fish.router)
app.include_router(admin.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    # dev-only: apply schema.sql
    schema_path = Path(__file__).parent / "db" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.execute(text(sql))
    
    # Start the daily scraper scheduler (Daily at 4 PM)
    scheduler.add_job(run_daily_scrape, "cron", hour=16, minute=0)
    scheduler.start()
    print("Background scheduler started: Daily scrape at 16:00.")

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()
    print("Background scheduler shut down.")

@app.get("/api/health")
def health():
    return {"status": "ok"}
