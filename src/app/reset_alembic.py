from sqlalchemy import text

from app.database.database import engine

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

print("✅ alembic_version table deleted.")