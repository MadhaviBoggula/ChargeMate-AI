"""One-shot DB bootstrap: verify connectivity and enable pgvector.

Run from backend/:  .venv\\Scripts\\python.exe scripts\\setup_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text

from app.core.config import get_settings


def engine_url() -> str:
    url = get_settings().database_url
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


def main() -> None:
    settings = get_settings()
    host = settings.database_url.split("@")[-1].split("/")[0]
    print(f"Connecting to {host} ...")
    engine = create_engine(engine_url(), pool_pre_ping=True)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        print(f"Connected: {version.split(',')[0]}")

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        version = conn.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).scalar()
        print(f"pgvector enabled, version: {version}")


if __name__ == "__main__":
    main()
