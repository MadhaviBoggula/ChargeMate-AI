from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.booking import AvailableSlot, StationAvailabilityOut
from app.schemas.station import StationDetailOut, StationOut
from app.services import booking_service, driver_service
from app.services.station_service import (
    get_active_station,
    search_stations,
)

router = APIRouter()


@router.get("", response_model=list[StationOut])
def list_stations(
    city: str | None = None,
    connector_type: str | None = None,
    charging_type: str | None = Query(
        default=None,
        pattern="^(AC|DC|ac|dc)$",
    ),
    min_power_kw: Decimal | None = Query(default=None, ge=0),
    max_price_per_kwh: Decimal | None = Query(default=None, ge=0),
    available_only: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Discover active charging stations with optional filters."""

    return search_stations(
        db,
        city=city,
        connector_type=connector_type,
        charging_type=charging_type,
        min_power_kw=min_power_kw,
        max_price_per_kwh=max_price_per_kwh,
        available_only=available_only,
        skip=skip,
        limit=limit,
    )


@router.get("/{station_id}", response_model=StationDetailOut)
def get_station(
    station_id: UUID,
    db: Session = Depends(get_db),
):
    """Return one active station with its chargers and connectors."""

    return get_active_station(db, station_id)


@router.get(
    "/{station_id}/availability",
    response_model=StationAvailabilityOut,
)
def get_station_availability(
    station_id: UUID,
    db: Session = Depends(get_db),
):
    """Return database-derived charger availability for a station."""

    return driver_service.station_availability(db, station_id)


@router.get(
    "/{station_id}/available-slots",
    response_model=list[AvailableSlot],
)
def get_available_slots(
    station_id: UUID,
    day: date | None = Query(default=None, alias="date"),
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    duration_minutes: int = Query(default=30, ge=30, le=240),
    connector_type: str | None = None,
    charging_type: str | None = Query(
        default=None,
        pattern="^(AC|DC|ac|dc)$",
    ),
    max_price_per_kwh: Decimal | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Search bookable slots for one station."""

    return booking_service.search_available_slots(
        db,
        station_id,
        start_at=start_at,
        end_at=end_at,
        day=day,
        duration_minutes=duration_minutes,
        connector_type=connector_type,
        charging_type=charging_type,
        max_price_per_kwh=max_price_per_kwh,
        limit=limit,
    )
