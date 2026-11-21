from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class DriverPreference(BaseModel):
    """Persistent charging preferences for one driver."""

    __tablename__ = "driver_preferences"

    __table_args__ = (
        CheckConstraint(
            "preferred_charging_type IS NULL OR "
            "preferred_charging_type IN ('AC', 'DC')",
            name="driver_preference_charging_type_valid",
        ),
        CheckConstraint(
            "max_price_per_kwh IS NULL OR max_price_per_kwh >= 0",
            name="driver_preference_price_nonnegative",
        ),
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    preferred_connector_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    preferred_charging_type: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

    max_price_per_kwh: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    preferred_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    default_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )

    driver: Mapped["User"] = relationship("User")
