from sqlalchemy.orm import Session

from app.driver.models import (
    Driver,
    DriverVehicle,
    FavoriteStation
)



# CREATE DRIVER

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



# GET ALL DRIVERS

def get_all_drivers(
    db: Session
):

    return db.query(Driver).all()



# GET SINGLE DRIVER

def get_driver(
    db: Session,
    driver_id:int
):

    return (
        db.query(Driver)
        .filter(
            Driver.id == driver_id
        )
        .first()
    )



# CREATE VEHICLE

def create_vehicle(
    db: Session,
    vehicle
):

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


    return new_vehicle



# CREATE FAVORITE

def create_favorite(
    db: Session,
    favorite
):

    new_favorite = FavoriteStation(
        driver_id=favorite.driver_id,
        station_id=favorite.station_id
    )


    db.add(new_favorite)

    db.commit()

    db.refresh(new_favorite)


    return new_favorite

# --------------------------
# Get Driver With Vehicles
# --------------------------

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



# --------------------------
# Get Driver Vehicles
# --------------------------

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



# --------------------------
# Update Driver
# --------------------------

def update_driver(
    db: Session,
    driver_id: int,
    driver_data: DriverCreate
):

    driver = (
        db.query(Driver)
        .filter(
            Driver.id == driver_id
        )
        .first()
    )


    if driver:

        driver.full_name = driver_data.full_name
        driver.email = driver_data.email
        driver.phone = driver_data.phone


        db.commit()

        db.refresh(driver)


    return driver



# --------------------------
# Delete Driver
# --------------------------

def delete_driver(
    db: Session,
    driver_id: int
):

    driver = (
        db.query(Driver)
        .filter(
            Driver.id == driver_id
        )
        .first()
    )


    if driver:

        db.delete(driver)

        db.commit()


    return driver

def get_driver(db, driver_id):

    return db.query(Driver).filter(
        Driver.id == driver_id
    ).first()



def get_all_drivers(db):

    return db.query(Driver).all()



def update_driver(db, driver_id, data):

    driver = get_driver(db, driver_id)

    if not driver:
        return None

    for key, value in data.dict(exclude_unset=True).items():
        setattr(driver, key, value)

    db.commit()
    db.refresh(driver)

    return driver



def delete_driver(db, driver_id):

    driver = get_driver(db, driver_id)

    if not driver:
        return None

    db.delete(driver)
    db.commit()

    return driver