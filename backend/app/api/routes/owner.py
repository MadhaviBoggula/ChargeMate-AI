from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_owner_id
from app.database.session import get_db
from app.models.charger import Charger
from app.models.station import Station
from app.schemas.owner_charger import (
    OwnerChargerCreate,
    OwnerChargerResponse,
    OwnerChargerUpdate,
)
from app.schemas.owner_station import (
    OwnerStationCreate,
    OwnerStationResponse,
    OwnerStationUpdate,
)


router = APIRouter()


def get_owned_station(
    db: Session,
    owner_id: UUID,
    station_id: UUID,
) -> Station:
    """Return a station only if it belongs to the authenticated owner."""

    statement = select(Station).where(
        Station.id == station_id,
        Station.owner_id == owner_id,
    )

    station = db.scalar(statement)

    if station is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found.",
        )

    return station


def get_owned_charger(
    db: Session,
    owner_id: UUID,
    charger_id: int,
) -> Charger:
    """Return a charger only if its station belongs to the owner."""

    statement = (
        select(Charger)
        .join(Station, Charger.station_id == Station.id)
        .where(
            Charger.id == charger_id,
            Station.owner_id == owner_id,
        )
    )

    charger = db.scalar(statement)

    if charger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found.",
        )

    return charger


# ============================================================
# OWNER STATION APIs
# Existing station endpoints are preserved.
# ============================================================

@router.post(
    "/stations",
    response_model=OwnerStationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_station(
    station_data: OwnerStationCreate,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """Create a station owned by the authenticated owner."""

    station = Station(
        **station_data.model_dump(),
        owner_id=owner_id,
    )

    db.add(station)
    db.commit()
    db.refresh(station)

    return station


@router.get(
    "/stations",
    response_model=list[OwnerStationResponse],
)
def list_my_stations(
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """List all stations belonging to the authenticated owner."""

    statement = (
        select(Station)
        .where(Station.owner_id == owner_id)
        .order_by(Station.created_at.desc())
    )

    return db.scalars(statement).all()


@router.get(
    "/stations/{station_id}",
    response_model=OwnerStationResponse,
)
def get_my_station(
    station_id: UUID,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """Get one station belonging to the authenticated owner."""

    return get_owned_station(db, owner_id, station_id)


@router.put(
    "/stations/{station_id}",
    response_model=OwnerStationResponse,
)
def update_my_station(
    station_id: UUID,
    station_data: OwnerStationUpdate,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """Update a station belonging to the authenticated owner."""

    station = get_owned_station(db, owner_id, station_id)

    updates = station_data.model_dump(exclude_unset=True)

    new_available_slots = updates.get(
        "available_slots",
        station.available_slots,
    )
    new_total_slots = updates.get(
        "total_slots",
        station.total_slots,
    )

    if new_available_slots > new_total_slots:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Available slots cannot exceed total slots.",
        )

    for field, value in updates.items():
        setattr(station, field, value)

    db.commit()
    db.refresh(station)

    return station


@router.delete(
    "/stations/{station_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deactivate_my_station(
    station_id: UUID,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """Deactivate a station without deleting its booking history."""

    station = get_owned_station(db, owner_id, station_id)

    station.is_active = False

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================
# OWNER CHARGER APIs
# ============================================================

@router.post(
    "/chargers",
    response_model=OwnerChargerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_charger(
    charger_data: OwnerChargerCreate,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """Create a charger under one of the owner's stations."""

    get_owned_station(
        db,
        owner_id,
        charger_data.station_id,
    )

    charger = Charger(**charger_data.model_dump())

    db.add(charger)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Could not create charger. Check whether the charger code "
                "already exists and whether the supplied values are valid."
            ),
        )

    db.refresh(charger)

    return charger


@router.get(
    "/chargers",
    response_model=list[OwnerChargerResponse],
)
def list_my_chargers(
    station_id: UUID | None = None,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """List chargers belonging to the authenticated owner's stations."""

    statement = (
        select(Charger)
        .join(Station, Charger.station_id == Station.id)
        .where(Station.owner_id == owner_id)
        .order_by(Charger.created_at.desc())
    )

    if station_id is not None:
        statement = statement.where(
            Charger.station_id == station_id
        )

    return db.scalars(statement).all()


@router.get(
    "/chargers/{charger_id}",
    response_model=OwnerChargerResponse,
)
def get_my_charger(
    charger_id: int,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """Get a charger belonging to one of the owner's stations."""

    return get_owned_charger(
        db,
        owner_id,
        charger_id,
    )


@router.patch(
    "/chargers/{charger_id}",
    response_model=OwnerChargerResponse,
)
def update_my_charger(
    charger_id: int,
    charger_data: OwnerChargerUpdate,
    db: Session = Depends(get_db),
    owner_id: UUID = Depends(get_owner_id),
):
    """Update a charger belonging to one of the owner's stations."""

    charger = get_owned_charger(
        db,
        owner_id,
        charger_id,
    )

    updates = charger_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(charger, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not update charger. Check the supplied values.",
        )

    db.refresh(charger)

    return charger
