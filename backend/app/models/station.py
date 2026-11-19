
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    Integer,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel
from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class ChargingStation(BaseModel):
    __tablename__ = "stations"

    __table_args__ = (
        CheckConstraint(
            "power > 0",
            name="station_power_positive",
        ),
        CheckConstraint(
            "available_slots >= 0",
            name="station_available_slots_nonnegative",
        ),
        CheckConstraint(
            "total_slots >= 0",
            name="station_total_slots_nonnegative",
        ),
        CheckConstraint(
            "available_slots <= total_slots",
            name="station_available_not_above_total",
        ),
        CheckConstraint(
            "price_per_kwh >= 0",
            name="station_price_nonnegative",
        ),
    )

    # Nullable initially to preserve existing station records.
    address_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("addresses.id"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[UUID | None] = mapped_column(
    PG_UUID(as_uuid=True),
    ForeignKey("users.id"),
    nullable=True,
    index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(255), nullable=True
    )

    # Preserve existing textual address.
    address: Mapped[str] = mapped_column(
        String(500), nullable=True
    )

    connectors: Mapped[list[str]] = mapped_column(
        JSON, nullable=True
    )

    charger_type: Mapped[str] = mapped_column(
        String(2), nullable=True
    )

    power: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    speed: Mapped[str] = mapped_column(
        String(20), nullable=True
    )

    available_slots: Mapped[int] = mapped_column(
        nullable=False
    )

    total_slots: Mapped[int] = mapped_column(
        nullable=True
    )

    price_per_kwh: Mapped[float] = mapped_column(
        Float, nullable=True
    )

    description: Mapped[str] = mapped_column(
        String(1000), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    address_record: Mapped["Address | None"] = relationship(
        "Address",
        back_populates="stations",
    )

    chargers: Mapped[list["Charger"]] = relationship(
        "Charger",
        back_populates="station",
    )
