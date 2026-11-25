from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.driver_vehicle import DriverVehicle
from app.models.favorite_station import FavoriteStation
from app.models.station import Station
from app.models.user import User, UserRole
from app.schemas.driver import (
    FavoriteCreate,
    FavoriteResponse,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)

router = APIRouter(tags=["Driver"])


def require_driver(user: User) -> None:
    if user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can access this resource.",
        )


@router.post(
    "/vehicles",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    vehicle = DriverVehicle(user_id=user.id, **payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/vehicles", response_model=list[VehicleResponse])
def list_vehicles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)
    return (
        db.query(DriverVehicle)
        .filter(DriverVehicle.user_id == user.id)
        .order_by(DriverVehicle.created_at.desc())
        .all()
    )


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    vehicle = (
        db.query(DriverVehicle)
        .filter(
            DriverVehicle.id == vehicle_id,
            DriverVehicle.user_id == user.id,
        )
        .first()
    )
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle(
    vehicle_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    vehicle = (
        db.query(DriverVehicle)
        .filter(
            DriverVehicle.id == vehicle_id,
            DriverVehicle.user_id == user.id,
        )
        .first()
    )
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    db.delete(vehicle)
    db.commit()
    return {"message": "Vehicle deleted successfully."}


@router.post(
    "/favorites",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    station = db.get(Station, payload.station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found.")

    existing = (
        db.query(FavoriteStation)
        .filter(
            FavoriteStation.user_id == user.id,
            FavoriteStation.station_id == payload.station_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Station is already in your favorites.",
        )

    favorite = FavoriteStation(
        user_id=user.id,
        station_id=payload.station_id,
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.get("/favorites", response_model=list[FavoriteResponse])
def list_favorites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)
    return (
        db.query(FavoriteStation)
        .filter(FavoriteStation.user_id == user.id)
        .order_by(FavoriteStation.created_at.desc())
        .all()
    )


@router.delete("/favorites/{favorite_id}")
def remove_favorite(
    favorite_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_driver(user)

    favorite = (
        db.query(FavoriteStation)
        .filter(
            FavoriteStation.id == favorite_id,
            FavoriteStation.user_id == user.id,
        )
        .first()
    )
    if favorite is None:
        raise HTTPException(status_code=404, detail="Favorite not found.")

    db.delete(favorite)
    db.commit()
    return {"message": "Favorite station removed successfully."}
