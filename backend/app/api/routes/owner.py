from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_owner_id
from app.database.session import get_db
from app.schemas.station import (
    ChargerCreate,
    ChargerOut,
    ChargerPriceUpdate,
    ChargerStatusUpdate,
    ChargerUpdate,
    ChargingSessionOut,
    OwnerAnalytics,
    RevenueSummary,
    StationAnalytics,
    StationCreate,
    StationDetailOut,
    StationOut,
    StationUpdate,
)
from app.services import owner_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Stations
# ---------------------------------------------------------------------------


@router.post(
    "/stations",
    response_model=StationDetailOut,
    status_code=status.HTTP_201_CREATED,
)
def create_station(
    payload: StationCreate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Create a station, optionally with chargers and connectors."""

    return owner_service.create_station(db, owner_id, payload)


@router.get("/stations", response_model=list[StationOut])
def list_stations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=200),
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """List every station owned by the authenticated owner."""

    return owner_service.list_owned_stations(
        db,
        owner_id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/stations/{station_id}",
    response_model=StationDetailOut,
)
def get_station(
    station_id: UUID,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Return one station owned by the authenticated owner."""

    return owner_service.get_owned_station(db, owner_id, station_id)


@router.patch(
    "/stations/{station_id}",
    response_model=StationDetailOut,
)
def update_station(
    station_id: UUID,
    payload: StationUpdate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Update station profile and address fields."""

    return owner_service.update_station(
        db,
        owner_id,
        station_id,
        payload,
    )


@router.delete(
    "/stations/{station_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_station(
    station_id: UUID,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Soft-delete a station by marking it inactive."""

    owner_service.deactivate_station(db, owner_id, station_id)


# ---------------------------------------------------------------------------
# Chargers
# ---------------------------------------------------------------------------


@router.post(
    "/stations/{station_id}/chargers",
    response_model=ChargerOut,
    status_code=status.HTTP_201_CREATED,
)
def create_charger(
    station_id: UUID,
    payload: ChargerCreate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Add a charger and its connectors to an owned station."""

    return owner_service.create_charger(
        db,
        owner_id,
        station_id,
        payload,
    )


@router.get("/chargers", response_model=list[ChargerOut])
def list_chargers(
    station_id: UUID | None = None,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """List chargers across the owner's network."""

    return owner_service.list_owned_chargers(
        db,
        owner_id,
        station_id=station_id,
    )


@router.get("/chargers/{charger_id}", response_model=ChargerOut)
def get_charger(
    charger_id: UUID,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Return one charger owned by the authenticated owner."""

    return owner_service.get_owned_charger(db, owner_id, charger_id)


@router.patch("/chargers/{charger_id}", response_model=ChargerOut)
def update_charger(
    charger_id: UUID,
    payload: ChargerUpdate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Update charger configuration and connectors."""

    return owner_service.update_charger(
        db,
        owner_id,
        charger_id,
        payload,
    )


@router.patch(
    "/chargers/{charger_id}/status",
    response_model=ChargerOut,
)
def update_charger_status(
    charger_id: UUID,
    payload: ChargerStatusUpdate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Set the operational status of a charger."""

    return owner_service.set_charger_status(
        db,
        owner_id,
        charger_id,
        payload.status,
    )


@router.patch(
    "/chargers/{charger_id}/price",
    response_model=ChargerOut,
)
def update_charger_price(
    charger_id: UUID,
    payload: ChargerPriceUpdate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Set the per-kWh price of a charger."""

    return owner_service.set_charger_price(
        db,
        owner_id,
        charger_id,
        payload.price_per_kwh,
    )


# ---------------------------------------------------------------------------
# Sessions, revenue, and analytics
# ---------------------------------------------------------------------------


@router.get("/sessions", response_model=list[ChargingSessionOut])
def list_sessions(
    station_id: UUID | None = None,
    charger_id: UUID | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    session_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(active|completed|cancelled|failed)$",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """List charging sessions across the owner's network."""

    return owner_service.list_sessions(
        db,
        owner_id,
        station_id=station_id,
        charger_id=charger_id,
        start_at=start_at,
        end_at=end_at,
        status=session_status,
        skip=skip,
        limit=limit,
    )


@router.get("/revenue", response_model=RevenueSummary)
def get_revenue(
    station_id: UUID | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Return revenue for one station or the whole owner network."""

    if station_id is not None:
        return owner_service.station_revenue(
            db,
            owner_id,
            station_id,
            start_at=start_at,
            end_at=end_at,
        )

    analytics = owner_service.owner_analytics(
        db,
        owner_id,
        start_at=start_at,
        end_at=end_at,
    )

    return RevenueSummary(
        station_id=None,
        start_at=start_at,
        end_at=end_at,
        session_count=analytics.session_count,
        total_energy_kwh=analytics.total_energy_kwh,
        total_revenue=analytics.total_revenue,
    )


@router.get(
    "/stations/{station_id}/revenue",
    response_model=RevenueSummary,
)
def get_station_revenue(
    station_id: UUID,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Return revenue for a single owned station."""

    return owner_service.station_revenue(
        db,
        owner_id,
        station_id,
        start_at=start_at,
        end_at=end_at,
    )


@router.get("/analytics", response_model=OwnerAnalytics)
def get_analytics(
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Return network-wide analytics derived from completed sessions."""

    return owner_service.owner_analytics(
        db,
        owner_id,
        start_at=start_at,
        end_at=end_at,
    )


@router.get(
    "/stations/{station_id}/analytics",
    response_model=StationAnalytics,
)
def get_station_analytics(
    station_id: UUID,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    """Return analytics for a single owned station."""

    return owner_service.station_analytics(
        db,
        owner_id,
        station_id,
        start_at=start_at,
        end_at=end_at,
    )
