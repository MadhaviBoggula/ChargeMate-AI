from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import (
    get_current_user,
    get_current_admin,
    get_current_driver,
    get_current_operator
)
from app.driver.schemas import (
    DriverCreate,
    DriverUpdate,
    DriverVehicleCreate,
     FavoriteStationCreate
)

from app.driver.repository import (
    create_driver,
    get_all_drivers,
    get_driver,
    create_vehicle,
    create_favorite,
    get_driver_with_vehicle,
    get_driver_vehicles,
    get_favorite_stations,
    delete_favorite_station,
    update_driver,
    delete_driver,
)

router = APIRouter(
    prefix="/drivers",
    tags=["Drivers"]
)


# ---------------------------------
# Create Driver API
# ---------------------------------

@router.post("/")
def create_driver_api(
    driver: DriverCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    return create_driver(
        db,
        driver
    )


# ---------------------------------
# Get All Drivers API
# ---------------------------------

@router.get("/")
def get_all_drivers_api(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    return get_all_drivers(db)


# ---------------------------------
# Get Driver By ID API
# ---------------------------------

@router.get("/{driver_id}")
def get_driver_api(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    driver = get_driver(
        db,
        driver_id
    )

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver not found"
        )

    return driver


# ---------------------------------
# Create Vehicle API
# ---------------------------------

@router.post("/vehicle")
def create_vehicle_api(
    vehicle: DriverVehicleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):

    return create_vehicle(
        db,
        vehicle
    )
# ---------------------------------
# Add Favorite Station
# ---------------------------------

@router.post("/favorites")
def create_favorite_api(
    favorite: FavoriteStationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    return create_favorite(
        db,
        favorite
    )


# ---------------------------------
# Get Favorite Stations
# ---------------------------------

@router.get("/{driver_id}/favorites")
def get_favorite_stations_api(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):
    return get_favorite_stations(
        db,
        driver_id
    )


# ---------------------------------
# Delete Favorite Station
# ---------------------------------

@router.delete("/favorites/{favorite_id}")
def delete_favorite_station_api(
    favorite_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_driver)
):

    result = delete_favorite_station(
        db,
        favorite_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Favorite station not found"
        )

    return {
        "message": "Favorite station deleted successfully"
    }

# ---------------------------------
# Get Driver Details API
# ---------------------------------

@router.get("/{driver_id}/details")
def get_driver_details_api(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    driver = get_driver_with_vehicle(
        db,
        driver_id
    )

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver not found"
        )

    return driver


# ---------------------------------
# Get Driver Vehicles API
# ---------------------------------

@router.get("/{driver_id}/vehicles")
def get_driver_vehicle_api(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    return get_driver_vehicles(
        db,
        driver_id
    )


# ---------------------------------
# Update Driver API
# ---------------------------------

@router.put("/{driver_id}")
def update_driver_api(
    driver_id: int,
    driver: DriverUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    result = update_driver(
        db,
        driver_id,
        driver
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Driver not found"
        )

    return result


# ---------------------------------
# Delete Driver API
# ---------------------------------

@router.delete("/{driver_id}")
def delete_driver_api(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):

    result = delete_driver(
        db,
        driver_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Driver not found"
        )

    return {
        "message": "Driver deleted successfully"
    }