from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Booking(Base):

    __tablename__ = "bookings"

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
        ForeignKey("stations.id"),
        nullable=False
    )

    booking_time = Column(
        DateTime,
        nullable=False
    )

    status = Column(
        String,
        default="Pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    driver = relationship("Driver")
    station = relationship("Station")