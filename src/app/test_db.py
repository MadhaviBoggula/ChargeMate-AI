from sqlalchemy import text

from app.database.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print("✅ Connected to Neon PostgreSQL")
        print(result.scalar())
except Exception as e:
    print("❌ Connection failed")
    print(e)