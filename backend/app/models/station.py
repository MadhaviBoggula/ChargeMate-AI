from sqlalchemy import Boolean, CheckConstraint, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseModel


class Station(BaseModel):
    __tablename__ = "stations"

    __table_args__ = (
        CheckConstraint("power > 0", name="station_power_positive"),
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

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    connectors: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    charger_type: Mapped[str] = mapped_column(String(2), nullable=False)
    power: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[str] = mapped_column(String(20), nullable=False)
    available_slots: Mapped[int] = mapped_column(nullable=False)
    total_slots: Mapped[int] = mapped_column(nullable=False)
    price_per_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )