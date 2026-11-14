from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Base class for all models
Base = declarative_base()



# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()