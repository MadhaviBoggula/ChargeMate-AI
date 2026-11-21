from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.connector import Connector
from app.models.station import ChargingStation
from app.schemas.station import (
    ChargerCreate,
    ChargerUpdate,
    OwnerAnalytics,
    RevenueSummary,
    StationAnalytics,
    StationCreate,
    StationUpdate,
)
from app.services.station_service import station_load_options

MONEY = Decimal("0.01")
ENERGY = Decimal("0.001")


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _decimal(value, places: Decimal = MONEY) -> Decimal:
    if value is None:
        return Decimal("0").quantize(places)
    return Decimal(str(value)).quantize(places)


def _owned_station(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
) -> ChargingStation:
    statement = (
        select(ChargingStation)
        .options(*station_load_options())
        .where(
            ChargingStation.id == station_id,
            ChargingStation.owner_id == owner_id,
        )
    )
    station = db.scalar(statement)

    if station is None:
        raise NotFoundError("Station not found.")

    return station


def list_owned_stations(
    db: Session,
    owner_id: UUID,
    *,
    skip: int = 0,
    limit: int = 200,
) -> list[ChargingStation]:
    statement = (
        select(ChargingStation)
        .options(*station_load_options())
        .where(ChargingStation.owner_id == owner_id)
        .order_by(ChargingStation.name)
        .offset(max(skip, 0))
        .limit(min(max(limit, 1), 200))
    )
    return list(db.scalars(statement).all())


def get_owned_station(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
) -> ChargingStation:
    return _owned_station(db, owner_id, station_id)


def _build_charger(payload: ChargerCreate) -> Charger:
    connector_types = [item.connector_type for item in payload.connectors]
    if len(connector_types) != len(set(connector_types)):
        raise ValidationError(
            "A charger cannot expose duplicate connector types."
        )

    charger = Charger(
        charger_code=payload.charger_code,
        charging_type=payload.charging_type,
        power_kw=payload.power_kw,
        status=payload.status,
        availability=payload.availability,
        price_per_kwh=payload.price_per_kwh,
    )
    charger.connectors = [
        Connector(**item.model_dump()) for item in payload.connectors
    ]
    return charger


def create_station(
    db: Session,
    owner_id: UUID,
    payload: StationCreate,
) -> ChargingStation:
    station = ChargingStation(
        owner_id=owner_id,
        name=payload.name,
        description=payload.description,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timezone=payload.timezone,
        is_active=payload.is_active,
    )
    station.chargers = [
        _build_charger(charger) for charger in payload.chargers
    ]

    db.add(station)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Station or charger data conflicts with an existing record."
        ) from exc

    return _owned_station(db, owner_id, station.id)


def update_station(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
    payload: StationUpdate,
) -> ChargingStation:
    station = _owned_station(db, owner_id, station_id)
    data = payload.model_dump(exclude_unset=True)

    required_fields = {
        "name",
        "city",
        "state",
        "pincode",
        "timezone",
        "is_active",
    }

    for key, value in data.items():
        if key in required_fields and value is None:
            raise ValidationError(f"{key} cannot be null.")
        setattr(station, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Station update conflicts with an existing record."
        ) from exc

    return _owned_station(db, owner_id, station_id)


def deactivate_station(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
) -> None:
    station = _owned_station(db, owner_id, station_id)
    station.is_active = False
    db.commit()


def _owned_charger(
    db: Session,
    owner_id: UUID,
    charger_id: UUID,
) -> Charger:
    statement = (
        select(Charger)
        .options(selectinload(Charger.connectors))
        .join(ChargingStation)
        .where(
            Charger.id == charger_id,
            ChargingStation.owner_id == owner_id,
        )
    )
    charger = db.scalar(statement)

    if charger is None:
        raise NotFoundError("Charger not found.")

    return charger


def list_owned_chargers(
    db: Session,
    owner_id: UUID,
    *,
    station_id: UUID | None = None,
) -> list[Charger]:
    statement = (
        select(Charger)
        .options(selectinload(Charger.connectors))
        .join(ChargingStation)
        .where(ChargingStation.owner_id == owner_id)
        .order_by(Charger.charger_code)
    )

    if station_id is not None:
        statement = statement.where(Charger.station_id == station_id)

    return list(db.scalars(statement).all())


def get_owned_charger(
    db: Session,
    owner_id: UUID,
    charger_id: UUID,
) -> Charger:
    return _owned_charger(db, owner_id, charger_id)


def create_charger(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
    payload: ChargerCreate,
) -> Charger:
    _owned_station(db, owner_id, station_id)
    charger = _build_charger(payload)
    charger.station_id = station_id
    db.add(charger)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Charger code or connector data already exists."
        ) from exc

    return _owned_charger(db, owner_id, charger.id)


def update_charger(
    db: Session,
    owner_id: UUID,
    charger_id: UUID,
    payload: ChargerUpdate,
) -> Charger:
    charger = _owned_charger(db, owner_id, charger_id)
    data = payload.model_dump(exclude_unset=True)
    connectors = data.pop("connectors", None)

    for key, value in data.items():
        if value is None:
            raise ValidationError(f"{key} cannot be null.")
        setattr(charger, key, value)

    if connectors is not None:
        connector_types = [
            item["connector_type"] for item in connectors
        ]
        if len(connector_types) != len(set(connector_types)):
            raise ValidationError(
                "A charger cannot expose duplicate connector types."
            )
        charger.connectors.clear()
        db.flush()
        charger.connectors.extend(
            Connector(**item) for item in connectors
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Charger update conflicts with an existing record."
        ) from exc

    return _owned_charger(db, owner_id, charger_id)


def set_charger_status(
    db: Session,
    owner_id: UUID,
    charger_id: UUID,
    status: str,
) -> Charger:
    charger = _owned_charger(db, owner_id, charger_id)
    charger.status = status
    db.commit()
    return _owned_charger(db, owner_id, charger_id)


def set_charger_price(
    db: Session,
    owner_id: UUID,
    charger_id: UUID,
    price_per_kwh: Decimal,
) -> Charger:
    charger = _owned_charger(db, owner_id, charger_id)
    charger.price_per_kwh = price_per_kwh
    db.commit()
    return _owned_charger(db, owner_id, charger_id)


def list_sessions(
    db: Session,
    owner_id: UUID,
    *,
    station_id: UUID | None = None,
    charger_id: UUID | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 200,
) -> list[ChargingSession]:
    statement = (
        select(ChargingSession)
        .join(ChargingStation)
        .where(ChargingStation.owner_id == owner_id)
        .order_by(ChargingSession.started_at.desc())
    )

    if station_id is not None:
        statement = statement.where(
            ChargingSession.station_id == station_id
        )
    if charger_id is not None:
        statement = statement.where(
            ChargingSession.charger_id == charger_id
        )
    if start_at is not None:
        statement = statement.where(
            ChargingSession.started_at >= _utc(start_at)
        )
    if end_at is not None:
        statement = statement.where(
            ChargingSession.started_at <= _utc(end_at)
        )
    if status is not None:
        statement = statement.where(ChargingSession.status == status)

    statement = (
        statement.offset(max(skip, 0))
        .limit(min(max(limit, 1), 500))
    )
    return list(db.scalars(statement).all())


def _aggregate_sessions(
    db: Session,
    owner_id: UUID,
    *,
    station_id: UUID | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> dict:
    statement = (
        select(
            func.count(ChargingSession.id),
            func.coalesce(func.sum(ChargingSession.energy_kwh), 0),
            func.coalesce(func.sum(ChargingSession.revenue), 0),
            func.coalesce(func.avg(ChargingSession.duration_minutes), 0),
            func.coalesce(func.sum(ChargingSession.duration_minutes), 0),
        )
        .join(ChargingStation)
        .where(
            ChargingStation.owner_id == owner_id,
            ChargingSession.status == "completed",
        )
    )

    if station_id is not None:
        statement = statement.where(
            ChargingSession.station_id == station_id
        )
    if start_at is not None:
        statement = statement.where(
            ChargingSession.started_at >= _utc(start_at)
        )
    if end_at is not None:
        statement = statement.where(
            ChargingSession.started_at <= _utc(end_at)
        )

    row = db.execute(statement).one()

    return {
        "session_count": int(row[0] or 0),
        "total_energy_kwh": _decimal(row[1], ENERGY),
        "total_revenue": _decimal(row[2], MONEY),
        "average_session_minutes": float(row[3] or 0),
        "total_session_minutes": int(row[4] or 0),
    }


def station_revenue(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> RevenueSummary:
    station = _owned_station(db, owner_id, station_id)
    totals = _aggregate_sessions(
        db,
        owner_id,
        station_id=station.id,
        start_at=start_at,
        end_at=end_at,
    )

    return RevenueSummary(
        station_id=station.id,
        start_at=_utc(start_at),
        end_at=_utc(end_at),
        session_count=totals["session_count"],
        total_energy_kwh=totals["total_energy_kwh"],
        total_revenue=totals["total_revenue"],
    )


def station_analytics(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> StationAnalytics:
    station = _owned_station(db, owner_id, station_id)
    totals = _aggregate_sessions(
        db,
        owner_id,
        station_id=station.id,
        start_at=start_at,
        end_at=end_at,
    )

    charger_count = len(station.chargers)
    period_minutes = _period_minutes(start_at, end_at)
    capacity = max(charger_count * period_minutes, 1)
    utilization = min(
        100.0,
        (totals["total_session_minutes"] / capacity) * 100,
    )

    return StationAnalytics(
        station_id=station.id,
        station_name=station.name,
        session_count=totals["session_count"],
        total_energy_kwh=totals["total_energy_kwh"],
        total_revenue=totals["total_revenue"],
        average_session_minutes=round(
            totals["average_session_minutes"], 2
        ),
        charger_count=charger_count,
        utilization_percent=round(utilization, 2),
    )


def owner_analytics(
    db: Session,
    owner_id: UUID,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> OwnerAnalytics:
    stations = list_owned_stations(db, owner_id, limit=200)
    station_metrics = [
        station_analytics(
            db,
            owner_id,
            station.id,
            start_at=start_at,
            end_at=end_at,
        )
        for station in stations
    ]

    session_count = sum(
        item.session_count for item in station_metrics
    )
    total_energy = sum(
        (item.total_energy_kwh for item in station_metrics),
        Decimal("0.000"),
    )
    total_revenue = sum(
        (item.total_revenue for item in station_metrics),
        Decimal("0.00"),
    )
    charger_count = sum(
        item.charger_count for item in station_metrics
    )
    average_revenue = (
        total_revenue / len(stations)
        if stations
        else Decimal("0.00")
    )

    return OwnerAnalytics(
        start_at=_utc(start_at),
        end_at=_utc(end_at),
        station_count=len(stations),
        charger_count=charger_count,
        session_count=session_count,
        total_energy_kwh=total_energy.quantize(ENERGY),
        total_revenue=total_revenue.quantize(MONEY),
        average_revenue_per_station=average_revenue.quantize(MONEY),
        stations=station_metrics,
    )


def _period_minutes(
    start_at: datetime | None,
    end_at: datetime | None,
) -> int:
    start = _utc(start_at)
    end = _utc(end_at)

    if start is None or end is None:
        return 30 * 24 * 60

    return max(int((end - start).total_seconds() / 60), 1)

