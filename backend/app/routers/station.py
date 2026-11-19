
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_owner_id
from app.database import get_db
from app.models.address import Address
from app.models.station import ChargingStation
from app.schemas.owner import StationCreate, StationUpdate, StationOut

router = APIRouter(
    prefix="/api/v1/stations",
    tags=["Charging Stations"],
)


@router.get("", response_model=list[StationOut])
def list_stations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return (
        db.query(ChargingStation)
        .filter(ChargingStation.is_active.is_(True))
        .offset(max(skip, 0))
        .limit(min(max(limit, 1), 200))
        .all()
    )


@router.get("/{station_id}", response_model=StationOut)
def get_station(
    station_id: UUID,
    db: Session = Depends(get_db),
):
    station = db.get(ChargingStation, station_id)

    if station is None or not station.is_active:
        raise HTTPException(
            status_code=404,
            detail="Station not found",
        )

    return station


@router.post(
    "",
    response_model=StationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_station(
    payload: StationCreate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    address = db.get(Address, payload.address_id)

    if address is None:
        raise HTTPException(
            status_code=404,
            detail="Address not found",
        )

    location = f"{address.city}, {address.state}"

    full_address = ", ".join(
        str(value)
        for value in [
            address.hno,
            address.street_village,
            address.city,
            address.state,
            address.pincode,
        ]
        if value is not None and str(value).strip()
    )

    station = ChargingStation(
        **payload.model_dump(),
        owner_id=owner_id,
        location=location,
        address=full_address,
    )

    db.add(station)

    try:
        db.commit()
        db.refresh(station)
    except Exception:
        db.rollback()
        raise

    return station


@router.patch("/{station_id}", response_model=StationOut)
def update_station(
    station_id: UUID,
    payload: StationUpdate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    station = (
        db.query(ChargingStation)
        .filter(
            ChargingStation.id == station_id,
            ChargingStation.owner_id == owner_id,
        )
        .first()
    )

    if station is None:
        raise HTTPException(
            status_code=404,
            detail="Station not found",
        )

    data = payload.model_dump(
        exclude_unset=True,
        exclude={"id", "owner_id"},
    )

    if data.get("address_id") is not None:
        if db.get(Address, data["address_id"]) is None:
            raise HTTPException(
                status_code=404,
                detail="Address not found",
            )

    for key, value in data.items():
        setattr(station, key, value)

    db.commit()
    db.refresh(station)

    return station


@router.delete("/{station_id}", status_code=204)
def delete_station(
    station_id: UUID,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    station = (
        db.query(ChargingStation)
        .filter(
            ChargingStation.id == station_id,
            ChargingStation.owner_id == owner_id,
        )
        .first()
    )

    if station is None:
        raise HTTPException(
            status_code=404,
            detail="Station not found",
        )

    # Soft delete preserves station and charger records.
    station.is_active = False
    db.commit()
