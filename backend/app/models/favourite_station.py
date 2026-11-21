from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class FavouriteStation(BaseModel):
    """A station saved by a driver."""

    __tablename__ = "favourite_stations"

    __table_args__ = (
        UniqueConstraint(
            "driver_id",
            "station_id",
            name="uq_favourite_stations_driver_station",
        ),
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

    driver: Mapped["User"] = relationship("User")

    station: Mapped["ChargingStation"] = relationship("ChargingStation")
