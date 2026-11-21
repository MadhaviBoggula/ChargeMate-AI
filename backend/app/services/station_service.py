from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models.charger import Charger
from app.models.connector import Connector
from app.models.station import ChargingStation


def station_load_options():
    return (
        selectinload(ChargingStation.chargers).selectinload(
            Charger.connectors
        ),
    )


def search_stations(
    db: Session,
    *,
    city: str | None = None,
    connector_type: str | None = None,
    charging_type: str | None = None,
    min_power_kw: Decimal | None = None,
    max_price_per_kwh: Decimal | None = None,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[ChargingStation]:
    statement = (
        select(ChargingStation)
        .options(*station_load_options())
        .join(ChargingStation.chargers)
        .join(Charger.connectors)
        .where(ChargingStation.is_active.is_(True))
    )

    if city:
        statement = statement.where(
            func.lower(ChargingStation.city) == city.lower()
        )
    if connector_type:
        statement = statement.where(
            func.lower(Connector.connector_type)
            == connector_type.lower()
        )
    if charging_type:
        statement = statement.where(
            Charger.charging_type == charging_type.upper()
        )
    if min_power_kw is not None:
        statement = statement.where(
            Charger.power_kw >= min_power_kw
        )
    if max_price_per_kwh is not None:
        statement = statement.where(
            Charger.price_per_kwh <= max_price_per_kwh
        )
    if available_only:
        statement = statement.where(
            Charger.status == "active",
            Charger.availability == "available",
            Connector.status == "active",
        )

    statement = (
        statement.distinct()
        .order_by(ChargingStation.name)
        .offset(max(skip, 0))
        .limit(min(max(limit, 1), 200))
    )

    return list(db.scalars(statement).all())


def get_active_station(
    db: Session,
    station_id: UUID,
) -> ChargingStation:
    statement = (
        select(ChargingStation)
        .options(*station_load_options())
        .where(
            ChargingStation.id == station_id,
            ChargingStation.is_active.is_(True),
        )
    )
    station = db.scalar(statement)

    if station is None:
        raise NotFoundError("Station not found.")

    return station
