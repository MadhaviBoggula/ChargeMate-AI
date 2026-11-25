from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from app.database.base import BaseModel


class DriverVehicle(BaseModel):
    __tablename__ = "driver_vehicles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    vehicle_number: Mapped[str] = mapped_column(
        String(30), nullable=False
    )
    vehicle_model: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    vehicle_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    manufacturing_year: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    battery_capacity: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    connector_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
