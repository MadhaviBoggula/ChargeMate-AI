from sqlalchemy.orm import Session

from app.driver.repository import (
    create_driver,
    get_driver,
    get_all_drivers,
    update_driver,
    delete_driver,
    create_vehicle,
    create_favorite,
    get_driver_with_vehicle,
    get_driver_vehicles,
    get_favorite_stations,
    delete_favorite_station,
)


# Driver Services

def create_driver_service(db: Session, driver):
    return create_driver(db, driver)


def get_driver_service(db: Session, driver_id: int):
    return get_driver(db, driver_id)


def get_all_drivers_service(db: Session):
    return get_all_drivers(db)


def update_driver_service(db: Session, driver_id: int, driver):
    return update_driver(db, driver_id, driver)


def delete_driver_service(db: Session, driver_id: int):
    return delete_driver(db, driver_id)


# Vehicle Services

def create_vehicle_service(db: Session, vehicle):
    return create_vehicle(db, vehicle)


def get_driver_with_vehicle_service(db: Session, driver_id: int):
    return get_driver_with_vehicle(db, driver_id)


def get_driver_vehicles_service(db: Session, driver_id: int):
    return get_driver_vehicles(db, driver_id)


# Favorite Station Services

def create_favorite_service(db: Session, favorite):
    return create_favorite(db, favorite)


def get_favorite_stations_service(db: Session, driver_id: int):
    return get_favorite_stations(db, driver_id)


def delete_favorite_station_service(db: Session, favorite_id: int):
    return delete_favorite_station(db, favorite_id)