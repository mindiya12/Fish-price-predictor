import os
import sys
from sqlalchemy import text

# Add the root app directory to sys.path to import internal services
sys.path.append("/app")

from app.db.session import engine

def test_conn():
    print(f"Engine URL: {engine.url}")
    try:
        with engine.connect() as conn:
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            print(f"Connected to DB: {db_name}")
            
            # Test INSERT
            print("Testing INSERT...")
            from datetime import date
            test_date = date(1990, 1, 1)
            conn.execute(text("""
                INSERT INTO price_history (date, price, location, fish, source)
                VALUES (:date, :price, 'test', 'test', 'test')
                ON CONFLICT (date, location, fish) DO NOTHING
            """), {"date": test_date, "price": 0.0})
            print("INSERT success!")
            
            # List all tables in public schema
            tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
            print(f"Tables via SQL: {[r[0] for r in tables]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_conn()
