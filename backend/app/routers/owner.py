from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
#from app.dependencies import get_owner_id
from app.api.deps import get_owner_id
from app.models.address import Address
from app.models.station import Station
from app.models.charger import Charger
from app.schemas.owner import StationCreate, StationUpdate, StationOut, ChargerCreate, ChargerUpdate, ChargerOut

router = APIRouter(prefix="/api/v1/owner", tags=["Owner - Stations & Chargers"])

def owned_station(db: Session, station_id: int, owner_id: int):
    station = db.query(ChargingStation).filter_by(id=station_id, owner_id=owner_id).first()
    if not station: raise HTTPException(404, "Station not found")
    return station

@router.post("/stations", response_model=StationOut, status_code=201)
def create_station(payload: StationCreate, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    if not db.get(Address, payload.address_id):
        raise HTTPException(404, "Address not found")
    obj = ChargingStation(owner_id=owner_id, **payload.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@router.get("/stations", response_model=list[StationOut])
def list_stations(owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    return db.query(ChargingStation).filter_by(owner_id=owner_id).all()

@router.get("/stations/{station_id}", response_model=StationOut)
def get_station(station_id: int, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    return owned_station(db, station_id, owner_id)

@router.patch("/stations/{station_id}", response_model=StationOut)
def update_station(station_id: int, payload: StationUpdate, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    obj = owned_station(db, station_id, owner_id)
    data = payload.model_dump(exclude_unset=True)
    if "address_id" in data and not db.get(Address, data["address_id"]):
        raise HTTPException(404, "Address not found")
    for key, value in data.items(): setattr(obj, key, value)
    db.commit(); db.refresh(obj)
    return obj

@router.post("/chargers", response_model=ChargerOut, status_code=201)
def create_charger(payload: ChargerCreate, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    owned_station(db, payload.station_id, owner_id)
    obj = Charger(**payload.model_dump())
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(409, "Could not create charger; check unique charger_code and field values")
    db.refresh(obj)
    return obj

@router.get("/chargers", response_model=list[ChargerOut])
def list_chargers(station_id: int | None = None, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    q = db.query(Charger).join(ChargingStation).filter(ChargingStation.owner_id == owner_id)
    if station_id is not None: q = q.filter(Charger.station_id == station_id)
    return q.all()

@router.get("/chargers/{charger_id}", response_model=ChargerOut)
def get_charger(charger_id: int, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    obj = db.query(Charger).join(ChargingStation).filter(Charger.id == charger_id, ChargingStation.owner_id == owner_id).first()
    if not obj: raise HTTPException(404, "Charger not found")
    return obj

@router.patch("/chargers/{charger_id}", response_model=ChargerOut)
def update_charger(charger_id: int, payload: ChargerUpdate, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    obj = db.query(Charger).join(ChargingStation).filter(Charger.id == charger_id, ChargingStation.owner_id == owner_id).first()
    if not obj: raise HTTPException(404, "Charger not found")
    data = payload.model_dump(exclude_unset=True)
    if "charging_type" in data and data["charging_type"] is not None:
        data["charging_type"] = data["charging_type"].upper()
        if data["charging_type"] not in {"AC", "DC"}: raise HTTPException(422, "charging_type must be AC or DC")
    if "status" in data and data["status"] not in {None, "active", "inactive", "maintenance", "faulted"}:
        raise HTTPException(422, "Invalid status")
    if "availability" in data and data["availability"] not in {None, "available", "occupied", "unavailable"}:
        raise HTTPException(422, "Invalid availability")
    for key, value in data.items(): setattr(obj, key, value)
    db.commit(); db.refresh(obj)
    return obj

@router.patch("/chargers/{charger_id}/status", response_model=ChargerOut)
def update_charger_status(charger_id: int, status_value: str, owner_id: int = Depends(get_owner_id), db: Session = Depends(get_db)):
    if status_value not in {"active", "inactive", "maintenance", "faulted"}:
        raise HTTPException(422, "Invalid status")
    obj = db.query(Charger).join(ChargingStation).filter(Charger.id == charger_id, ChargingStation.owner_id == owner_id).first()
    if not obj: raise HTTPException(404, "Charger not found")
    obj.status = status_value
    db.commit(); db.refresh(obj)
    return obj
