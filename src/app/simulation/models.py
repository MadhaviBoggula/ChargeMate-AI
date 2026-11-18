from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func

from app.database.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(120),
        nullable=False
    )

    description = Column(
        String,
        nullable=False
    )

    initial_state = Column(
        JSON,
        nullable=False
    )

    current_state = Column(
        JSON,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )