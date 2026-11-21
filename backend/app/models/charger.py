from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

CHARGER_STATUSES = ("active", "inactive", "maintenance", "faulted")
CHARGER_AVAILABILITY = ("available", "occupied", "unavailable")


class Charger(BaseModel):
    """An individual charging unit belonging to a station."""

    __tablename__ = "chargers"

    __table_args__ = (
        UniqueConstraint(
            "charger_code",
            name="uq_chargers_charger_code",
        ),
        CheckConstraint(
            "charging_type IN ('AC', 'DC')",
            name="charger_charging_type_valid",
        ),
        CheckConstraint(
            "power_kw > 0",
            name="charger_power_positive",
        ),
        CheckConstraint(
            "price_per_kwh >= 0",
            name="charger_price_nonnegative",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'maintenance', 'faulted')",
            name="charger_status_valid",
        ),
        CheckConstraint(
            "availability IN ('available', 'occupied', 'unavailable')",
            name="charger_availability_valid",
        ),
    )

    station_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    charger_code: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    charging_type: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    power_kw: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        server_default="active",
        nullable=False,
        index=True,
    )

    availability: Mapped[str] = mapped_column(
        String(20),
        default="available",
        server_default="available",
        nullable=False,
        index=True,
    )

    price_per_kwh: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        server_default="0.00",
        nullable=False,
    )

    station: Mapped["ChargingStation"] = relationship(
        "ChargingStation",
        back_populates="chargers",
    )

    connectors: Mapped[list["Connector"]] = relationship(
        "Connector",
        back_populates="charger",
        cascade="all, delete-orphan",
        order_by="Connector.connector_type",
    )

    sessions: Mapped[list["ChargingSession"]] = relationship(
        "ChargingSession",
        back_populates="charger",
    )
