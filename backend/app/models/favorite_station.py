from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseModel


class FavoriteStation(BaseModel):
    __tablename__ = "favorite_stations"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "station_id",
            name="uq_favorite_station_user_station",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    station_id: Mapped[UUID] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
