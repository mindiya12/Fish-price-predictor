from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from pathlib import Path
from app.api import history, forecast, download, fish

app = FastAPI(title="Fish Price API")

app.include_router(history.router)
app.include_router(forecast.router)
app.include_router(download.router)
app.include_router(fish.router)

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

@app.get("/api/health")
def health():
    return {"status": "ok"}
