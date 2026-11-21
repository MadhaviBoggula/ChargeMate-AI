from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class ChargingStation(BaseModel):
    """A charging station owned by one authenticated owner."""

    __tablename__ = "stations"

    __table_args__ = (
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="station_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="station_longitude_range",
        ),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    address_line1: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address_line2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    pincode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        default="Asia/Kolkata",
        server_default="Asia/Kolkata",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        index=True,
    )

    owner: Mapped["User"] = relationship("User")

    chargers: Mapped[list["Charger"]] = relationship(
        "Charger",
        back_populates="station",
        cascade="all, delete-orphan",
        order_by="Charger.charger_code",
    )

    @property
    def connector_types(self) -> list[str]:
        return sorted(
            {
                connector.connector_type
                for charger in self.chargers
                for connector in charger.connectors
            }
        )

    @property
    def min_price_per_kwh(self) -> Decimal | None:
        if not self.chargers:
            return None
        return min(charger.price_per_kwh for charger in self.chargers)

    @property
    def max_power_kw(self) -> Decimal | None:
        if not self.chargers:
            return None
        return max(charger.power_kw for charger in self.chargers)

    @property
    def total_chargers(self) -> int:
        return len(self.chargers)

    @property
    def available_chargers(self) -> int:
        return sum(
            1
            for charger in self.chargers
            if charger.status == "active"
            and charger.availability == "available"
        )
