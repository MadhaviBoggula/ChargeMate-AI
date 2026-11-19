
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_owner_id
from app.models.address import Address
from app.models.station import ChargingStation
from app.models.charger import Charger
from app.schemas.owner import (
    StationCreate,
    StationUpdate,
    StationOut,
    ChargerCreate,
    ChargerUpdate,
    ChargerOut,
)

router = APIRouter(
    prefix="/api/v1/owner",
    tags=["Owner - Stations & Chargers"],
)


def owned_station(
    db: Session,
    station_id: UUID,
    owner_id: UUID,
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

    return station


def get_address_details(db: Session, address_id: int):
    address = db.get(Address, address_id)

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

    return location, full_address


# -------------------------------
# STATION APIs
# -------------------------------

@router.post(
    "/stations",
    response_model=StationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_station(
    payload: StationCreate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    location, full_address = get_address_details(
        db, payload.address_id
    )

    data = payload.model_dump(
        exclude={"id", "owner_id", "location", "address"}
    )

    obj = ChargingStation(
        **data,
        owner_id=owner_id,
        location=location,
        address=full_address,
    )

    db.add(obj)

    try:
        db.commit()
        db.refresh(obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Station could not be created due to a database constraint",
        )

    return obj


@router.get("/stations", response_model=list[StationOut])
def list_stations(
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChargingStation)
        .filter(ChargingStation.owner_id == owner_id)
        .all()
    )


@router.get("/stations/{station_id}", response_model=StationOut)
def get_station(
    station_id: UUID,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    return owned_station(db, station_id, owner_id)


@router.patch("/stations/{station_id}", response_model=StationOut)
def update_station(
    station_id: UUID,
    payload: StationUpdate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    obj = owned_station(db, station_id, owner_id)

    data = payload.model_dump(
        exclude_unset=True,
        exclude={"id", "owner_id", "location", "address"},
    )

    if "address_id" in data:
        if data["address_id"] is None:
            raise HTTPException(
                status_code=422,
                detail="address_id cannot be null",
            )

        location, full_address = get_address_details(
            db, data["address_id"]
        )

        obj.location = location
        obj.address = full_address

    new_available = data.get(
        "available_slots", obj.available_slots
    )
    new_total = data.get(
        "total_slots", obj.total_slots
    )

    if (
        new_available is not None
        and new_total is not None
        and new_available > new_total
    ):
        raise HTTPException(
            status_code=422,
            detail="available_slots cannot exceed total_slots",
        )

    for key, value in data.items():
        setattr(obj, key, value)

    try:
        db.commit()
        db.refresh(obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Station update violates a database constraint",
        )

    return obj


# -------------------------------
# CHARGER APIs
# -------------------------------

@router.post(
    "/chargers",
    response_model=ChargerOut,
    status_code=status.HTTP_201_CREATED,
)
def create_charger(
    payload: ChargerCreate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    owned_station(db, payload.station_id, owner_id)

    data = payload.model_dump()

    obj = Charger(**data)
    db.add(obj)

    try:
        db.commit()
        db.refresh(obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not create charger; check charger_code and field values",
        )

    return obj


@router.get("/chargers", response_model=list[ChargerOut])
def list_chargers(
    station_id: UUID | None = None,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    q = (
        db.query(Charger)
        .join(ChargingStation)
        .filter(ChargingStation.owner_id == owner_id)
    )

    if station_id is not None:
        q = q.filter(Charger.station_id == station_id)

    return q.all()


@router.get("/chargers/{charger_id}", response_model=ChargerOut)
def get_charger(
    charger_id: int,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    obj = (
        db.query(Charger)
        .join(ChargingStation)
        .filter(
            Charger.id == charger_id,
            ChargingStation.owner_id == owner_id,
        )
        .first()
    )

    if obj is None:
        raise HTTPException(404, "Charger not found")

    return obj


@router.patch("/chargers/{charger_id}", response_model=ChargerOut)
def update_charger(
    charger_id: int,
    payload: ChargerUpdate,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    obj = (
        db.query(Charger)
        .join(ChargingStation)
        .filter(
            Charger.id == charger_id,
            ChargingStation.owner_id == owner_id,
        )
        .first()
    )

    if obj is None:
        raise HTTPException(404, "Charger not found")

    data = payload.model_dump(
        exclude_unset=True,
        exclude={"id"},
    )

    if "station_id" in data:
        if data["station_id"] is None:
            raise HTTPException(
                422, "station_id cannot be null"
            )
        owned_station(db, data["station_id"], owner_id)

    if "charging_type" in data:
        value = data["charging_type"]
        if value is None:
            raise HTTPException(
                422, "charging_type cannot be null"
            )
        value = value.upper()
        if value not in {"AC", "DC"}:
            raise HTTPException(
                422, "charging_type must be AC or DC"
            )
        data["charging_type"] = value

    if "status" in data:
        if data["status"] not in {
            "active", "inactive", "maintenance", "faulted"
        }:
            raise HTTPException(422, "Invalid status")

    if "availability" in data:
        if data["availability"] not in {
            "available", "occupied", "unavailable"
        }:
            raise HTTPException(422, "Invalid availability")

    for key, value in data.items():
        setattr(obj, key, value)

    try:
        db.commit()
        db.refresh(obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Charger update violates a database constraint"
        )

    return obj


@router.patch(
    "/chargers/{charger_id}/status",
    response_model=ChargerOut,
)
def update_charger_status(
    charger_id: int,
    status_value: str,
    owner_id: UUID = Depends(get_owner_id),
    db: Session = Depends(get_db),
):
    if status_value not in {
        "active", "inactive", "maintenance", "faulted"
    }:
        raise HTTPException(422, "Invalid status")

    obj = (
        db.query(Charger)
        .join(ChargingStation)
        .filter(
            Charger.id == charger_id,
            ChargingStation.owner_id == owner_id,
        )
        .first()
    )

    if obj is None:
        raise HTTPException(404, "Charger not found")

    obj.status = status_value

    try:
        db.commit()
        db.refresh(obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Could not update charger status"
        )

    return obj
