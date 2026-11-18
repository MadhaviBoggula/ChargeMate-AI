from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.auth.dependencies import (
    get_current_admin,
    get_current_operator,
    get_current_user
)

from app.stations.schemas import (
    StationCreate,
    StationUpdate
)

from app.stations.repository import (
    create_station,
    get_all_stations,
    get_station,
    update_station,
    delete_station
)

router = APIRouter(
    prefix="/stations",
    tags=["Stations"]
)


# -----------------------------
# Create Station
# -----------------------------
@router.post("/")
def create_station_api(
    station: StationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    return create_station(db, station)


# -----------------------------
# Get All Stations
# -----------------------------
@router.get("/")
def get_all_stations_api(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_all_stations(db)


# -----------------------------
# Get Station By ID
# -----------------------------
@router.get("/{station_id}")
def get_station_api(
    station_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    station = get_station(db, station_id)

    if not station:
        raise HTTPException(
            status_code=404,
            detail="Station not found"
        )

    return station


# -----------------------------
# Update Station
# -----------------------------
@router.put("/{station_id}")
def update_station_api(
    station_id: int,
    station: StationUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_operator)
):
    result = update_station(db, station_id, station)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Station not found"
        )

    return result


# -----------------------------
# Delete Station
# -----------------------------
@router.delete("/{station_id}")
def delete_station_api(
    station_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_admin)
):
    result = delete_station(db, station_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Station not found"
        )

    return {
        "message": "Station deleted successfully"
    }