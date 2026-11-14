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
)

from app.driver.repository import (
    create_driver,
    get_all_drivers,
    get_driver,
    create_vehicle,
    get_driver_with_vehicle,
    get_driver_vehicles,
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
    current_user=Depends(get_current_user)
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
    current_user=Depends(get_current_user)
):

    return get_all_drivers(db)


# ---------------------------------
# Get Driver By ID API
# ---------------------------------

@router.get("/{driver_id}")
def get_driver_api(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
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
# Get Driver Details API
# ---------------------------------

@router.get("/{driver_id}/details")
def get_driver_details_api(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
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
    current_user=Depends(get_current_user)
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
    current_user=Depends(get_current_user)
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
    current_user=Depends(get_current_user)
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