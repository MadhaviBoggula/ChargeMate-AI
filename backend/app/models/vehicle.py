from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class Vehicle(BaseModel):
    """A driver's EV, used for connector compatibility and bookings."""

    __tablename__ = "vehicles"

    __table_args__ = (
        UniqueConstraint(
            "driver_id",
            "registration_number",
            name="uq_vehicles_driver_registration",
        ),
        CheckConstraint(
            "manufacturing_year IS NULL OR "
            "(manufacturing_year >= 1950 AND manufacturing_year <= 2100)",
            name="vehicle_year_range",
        ),
        CheckConstraint(
            "battery_capacity_kwh IS NULL OR battery_capacity_kwh > 0",
            name="vehicle_battery_positive",
        ),
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    registration_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    nickname: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    vehicle_model: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        default="car",
        server_default="car",
        nullable=False,
    )

    manufacturing_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    battery_capacity_kwh: Mapped[Decimal | None] = mapped_column(
        Numeric(7, 2),
        nullable=True,
    )

    connector_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    driver: Mapped["User"] = relationship("User")
