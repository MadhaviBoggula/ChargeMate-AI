from sqlalchemy.orm import Session

from app.driver.models import (
    Driver,
    DriverVehicle,
    FavoriteStation
)

from app.driver.schemas import DriverCreate


# ---------------------------------
# Create Driver
# ---------------------------------

def create_driver(
    db: Session,
    driver
):

    new_driver = Driver(
        full_name=driver.full_name,
        email=driver.email,
        phone=driver.phone
    )

    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    return new_driver


# ---------------------------------
# Get All Drivers
# ---------------------------------

def get_all_drivers(
    db: Session
):

    return db.query(Driver).all()


# ---------------------------------
# Get Driver By ID
# ---------------------------------

def get_driver(
    db: Session,
    driver_id: int
):

    return (
        db.query(Driver)
        .filter(
            Driver.id == driver_id
        )
        .first()
    )


# ---------------------------------
# Create Vehicle
# ---------------------------------
def create_vehicle(
    db: Session,
    vehicle
):

    driver = (
        db.query(Driver)
        .filter(
            Driver.id == vehicle.driver_id
        )
        .first()
    )

    if not driver:
        return "driver_not_found"

    existing_vehicle = (
        db.query(DriverVehicle)
        .filter(
            DriverVehicle.vehicle_number == vehicle.vehicle_number
        )
        .first()
    )

    if existing_vehicle:
        return "vehicle_exists"

    new_vehicle = DriverVehicle(
        driver_id=vehicle.driver_id,
        vehicle_number=vehicle.vehicle_number,
        vehicle_model=vehicle.vehicle_model,
        vehicle_type=vehicle.vehicle_type,
        manufacturing_year=vehicle.manufacturing_year,
        battery_capacity=vehicle.battery_capacity,
        connector_type=vehicle.connector_type
    )

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return new_vehicle

# ---------------------------------
# Create Favorite Station
# ---------------------------------

def create_favorite(
    db: Session,
    favorite
):

    existing_favorite = (
        db.query(FavoriteStation)
        .filter(
            FavoriteStation.driver_id == favorite.driver_id,
            FavoriteStation.station_id == favorite.station_id
        )
        .first()
    )

    if existing_favorite:
        return None

    new_favorite = FavoriteStation(
        driver_id=favorite.driver_id,
        station_id=favorite.station_id
    )

    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    return new_favorite


# ---------------------------------
# Get Driver With Vehicles
# ---------------------------------

def get_driver_with_vehicle(
    db: Session,
    driver_id: int
):

    return (
        db.query(Driver)
        .filter(
            Driver.id == driver_id
        )
        .first()
    )


# ---------------------------------
# Get Driver Vehicles
# ---------------------------------

def get_driver_vehicles(
    db: Session,
    driver_id: int
):

    return (
        db.query(DriverVehicle)
        .filter(
            DriverVehicle.driver_id == driver_id
        )
        .all()
    )


# ---------------------------------
# Update Driver
# ---------------------------------

def update_driver(
    db: Session,
    driver_id: int,
    driver_data: DriverCreate
):

    driver = get_driver(
        db,
        driver_id
    )

    if not driver:
        return None

    driver.full_name = driver_data.full_name
    driver.email = driver_data.email
    driver.phone = driver_data.phone

    db.commit()
    db.refresh(driver)

    return driver


# ---------------------------------
# Delete Driver
# ---------------------------------

def delete_driver(
    db: Session,
    driver_id: int
):

    driver = get_driver(
        db,
        driver_id
    )

    if not driver:
        return None

    db.delete(driver)
    db.commit()

    return driver


# ---------------------------------
# Get Driver Favorite Stations
# ---------------------------------

def get_favorite_stations(
    db: Session,
    driver_id: int
):

    return (
        db.query(FavoriteStation)
        .filter(
            FavoriteStation.driver_id == driver_id
        )
        .all()
    )


# ---------------------------------
# Delete Favorite Station
# ---------------------------------

def delete_favorite_station(
    db: Session,
    favorite_id: int
):

    favorite = (
        db.query(FavoriteStation)
        .filter(
            FavoriteStation.id == favorite_id
        )
        .first()
    )

    if not favorite:
        return None

    db.delete(favorite)
    db.commit()

    return favorite