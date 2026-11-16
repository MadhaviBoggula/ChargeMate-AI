from sqlalchemy.orm import Session
from app.models.station import Station
from app.models.charger import Charger

def list_stations(db: Session, owner_id: int):
    return db.query(Station).filter_by(owner_id=owner_id).all()

def get_station(db: Session, owner_id: int, station_id: int):
    return db.query(Station).filter_by(owner_id=owner_id, id=station_id).first()

def list_chargers(db: Session, owner_id: int):
    return db.query(Charger).join(Station).filter(Station.owner_id == owner_id).all()

def set_charger_status(db: Session, owner_id: int, charger_id: int, status: str):
    if status not in {"active", "inactive", "maintenance", "faulted"}:
        raise ValueError("Invalid charger status")
    charger = db.query(Charger).join(Station).filter(
        Charger.id == charger_id, Station.owner_id == owner_id
    ).first()
    if not charger:
        return None
    charger.status = status
    db.commit()
    db.refresh(charger)
    return charger
