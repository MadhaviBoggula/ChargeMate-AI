
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseModel


class Booking(BaseModel):
    __tablename__ = "bookings"

    __table_args__ = (
        CheckConstraint(
            "duration_minutes IN (30, 60, 120)",
            name="ck_bookings_duration_minutes_allowed",
        ),
        CheckConstraint(
            "end_time > booking_time",
            name="ck_bookings_end_time_after_booking_time",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    station_id: Mapped[UUID] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    booking_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="Pending",
        server_default="Pending",
        nullable=False,
    )
