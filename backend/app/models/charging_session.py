from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

SESSION_STATUSES = ("active", "completed", "cancelled", "failed")


class ChargingSession(BaseModel):
    """A simulated charging session and its revenue snapshot."""

    __tablename__ = "charging_sessions"

    __table_args__ = (
        CheckConstraint(
            "energy_kwh >= 0",
            name="session_energy_nonnegative",
        ),
        CheckConstraint(
            "duration_minutes >= 0",
            name="session_duration_nonnegative",
        ),
        CheckConstraint(
            "price_per_kwh >= 0",
            name="session_price_nonnegative",
        ),
        CheckConstraint(
            "revenue >= 0",
            name="session_revenue_nonnegative",
        ),
        CheckConstraint(
            "status IN ('active', 'completed', 'cancelled', 'failed')",
            name="session_status_valid",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="session_end_after_start",
        ),
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

    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    energy_kwh: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        default=Decimal("0.000"),
        server_default="0.000",
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    price_per_kwh: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )

    revenue: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="completed",
        server_default="completed",
        nullable=False,
        index=True,
    )

    station: Mapped["ChargingStation"] = relationship("ChargingStation")

    charger: Mapped["Charger"] = relationship(
        "Charger",
        back_populates="sessions",
    )

    driver: Mapped["User | None"] = relationship("User")
