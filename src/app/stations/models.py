from sqlalchemy import Column, Integer, String, Float

from app.database.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)

    station_name = Column(String, nullable=False)

    location = Column(String, nullable=False)

    latitude = Column(Float, nullable=False)

    longitude = Column(Float, nullable=False)

    total_connectors = Column(Integer, nullable=False)

    available_connectors = Column(Integer, nullable=False)

    charging_speed = Column(String, nullable=False)

    status = Column(String, nullable=False)