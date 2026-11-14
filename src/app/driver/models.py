from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    phone = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


    vehicles = relationship(
        "DriverVehicle",
        back_populates="driver",
        cascade="all, delete"
    )


    favorites = relationship(
        "FavoriteStation",
        back_populates="driver",
        cascade="all, delete"
    )



class DriverVehicle(Base):

    __tablename__ = "driver_vehicles"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    driver_id = Column(
        Integer,
        ForeignKey("drivers.id"),
        nullable=False
    )


    vehicle_number = Column(
        String,
        nullable=False
    )


    vehicle_model = Column(
        String,
        nullable=False
    )


    vehicle_type = Column(
        String,
        nullable=False
    )


    manufacturing_year = Column(
        Integer,
        nullable=False
    )


    battery_capacity = Column(
        Integer,
        nullable=False
    )


    connector_type = Column(
        String,
        nullable=False
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


    driver = relationship(
        "Driver",
        back_populates="vehicles"
    )



class FavoriteStation(Base):

    __tablename__ = "favorite_stations"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    driver_id = Column(
        Integer,
        ForeignKey("drivers.id"),
        nullable=False
    )


    station_id = Column(
        Integer,
        nullable=False
    )


    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


    driver = relationship(
        "Driver",
        back_populates="favorites"
    )