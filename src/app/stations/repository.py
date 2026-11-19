from sqlalchemy.orm import Session

from app.stations.models import Station
from app.stations.schemas import StationCreate, StationUpdate


def create_station(
    db: Session,
    station: StationCreate
):

    existing_station = (
        db.query(Station)
        .filter(
            Station.station_name == station.station_name,
            Station.location == station.location
        )
        .first()
    )

    if existing_station:
        return None


    new_station = Station(
        station_name=station.station_name,
        location=station.location,
        latitude=station.latitude,
        longitude=station.longitude,
        total_connectors=station.total_connectors,
        available_connectors=station.available_connectors,
        charging_speed=station.charging_speed,
        status=station.status
    )

    db.add(new_station)
    db.commit()
    db.refresh(new_station)

    return new_station


def get_all_stations(db: Session):

    return db.query(Station).all()


def get_station(db: Session, station_id: int):

    return (
        db.query(Station)
        .filter(Station.id == station_id)
        .first()
    )


def update_station(
    db: Session,
    station_id: int,
    station: StationUpdate
):

    db_station = get_station(db, station_id)

    if not db_station:
        return None

    db_station.station_name = station.station_name
    db_station.location = station.location
    db_station.latitude = station.latitude
    db_station.longitude = station.longitude
    db_station.total_connectors = station.total_connectors
    db_station.available_connectors = station.available_connectors
    db_station.charging_speed = station.charging_speed
    db_station.status = station.status

    db.commit()
    db.refresh(db_station)

    return db_station


def delete_station(
    db: Session,
    station_id: int
):

    db_station = get_station(db, station_id)

    if not db_station:
        return None

    db.delete(db_station)
    db.commit()

    return db_station