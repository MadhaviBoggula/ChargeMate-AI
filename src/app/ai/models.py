from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from app.database.database import Base


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    station_id = Column(
        Integer,
        nullable=False
    )

    forecast_date = Column(
        String,
        nullable=False
    )

    predicted_demand = Column(
        Float,
        nullable=False
    )

    demand_level = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )