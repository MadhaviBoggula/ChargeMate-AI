from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

BOOKING_STATUSES = ("CONFIRMED", "CANCELLED", "COMPLETED", "EXPIRED")
DEFAULT_SLOT_MINUTES = 30


class ChargingBooking(BaseModel):
    """A simulated reservation of a charger for a fixed time interval."""

    __tablename__ = "charging_bookings"

    __table_args__ = (
        UniqueConstraint(
            "booking_reference",
            name="uq_charging_bookings_booking_reference",
        ),
        CheckConstraint(
            "status IN ('CONFIRMED', 'CANCELLED', 'COMPLETED', 'EXPIRED')",
            name="booking_status_valid",
        ),
        CheckConstraint(
            "end_at > start_at",
            name="booking_end_after_start",
        ),
        CheckConstraint(
            "estimated_price IS NULL OR estimated_price >= 0",
            name="booking_price_nonnegative",
        ),
        Index(
            "ix_charging_bookings_charger_start",
            "charger_id",
            "start_at",
        ),
    )

    booking_reference: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    charger_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chargers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )

    connector_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="CONFIRMED",
        server_default="CONFIRMED",
        nullable=False,
        index=True,
    )

    estimated_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    driver: Mapped["User"] = relationship("User")

    station: Mapped["ChargingStation"] = relationship("ChargingStation")

    charger: Mapped["Charger"] = relationship("Charger")

    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle")
