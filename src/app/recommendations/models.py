from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from app.database.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    station_id = Column(
        Integer,
        nullable=False
    )

    recommendation_type = Column(
        String(100),
        nullable=False
    )

    message = Column(
        String,
        nullable=False
    )

    priority = Column(
        String(50),
        nullable=False
    )

    confidence = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )