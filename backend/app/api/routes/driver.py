from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_driver_id
from app.database.session import get_db
from app.schemas.driver import (
    CompatibleStationOut,
    DriverPreferenceOut,
    DriverPreferenceUpdate,
    FavouriteStationOut,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
)
from app.schemas.station import StationOut
from app.services import driver_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------


@router.post(
    "/vehicles",
    response_model=VehicleOut,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle(
    payload: VehicleCreate,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Register a vehicle for the authenticated driver."""

    return driver_service.create_vehicle(db, driver_id, payload)


@router.get("/vehicles", response_model=list[VehicleOut])
def list_vehicles(
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """List the authenticated driver's vehicles."""

    return driver_service.list_vehicles(db, driver_id)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: UUID,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Return one of the authenticated driver's vehicles."""

    return driver_service.get_vehicle(db, driver_id, vehicle_id)


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Update one of the authenticated driver's vehicles."""

    return driver_service.update_vehicle(
        db,
        driver_id,
        vehicle_id,
        payload,
    )


@router.delete(
    "/vehicles/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_vehicle(
    vehicle_id: UUID,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Delete one of the authenticated driver's vehicles."""

    driver_service.delete_vehicle(db, driver_id, vehicle_id)


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------


@router.get("/preferences", response_model=DriverPreferenceOut)
def get_preferences(
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Return the driver's charging preferences."""

    return driver_service.get_or_create_preferences(db, driver_id)


@router.put("/preferences", response_model=DriverPreferenceOut)
def update_preferences(
    payload: DriverPreferenceUpdate,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Update the driver's charging preferences."""

    return driver_service.update_preferences(db, driver_id, payload)


# ---------------------------------------------------------------------------
# Favourite stations
# ---------------------------------------------------------------------------


@router.get("/favourites", response_model=list[FavouriteStationOut])
def list_favourites(
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """List the driver's saved stations."""

    return driver_service.list_favourites(db, driver_id)


@router.post(
    "/favourites/{station_id}",
    response_model=FavouriteStationOut,
    status_code=status.HTTP_201_CREATED,
)
def add_favourite(
    station_id: UUID,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Save an active station to the driver's favourites."""

    return driver_service.add_favourite(db, driver_id, station_id)


@router.delete(
    "/favourites/{station_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_favourite(
    station_id: UUID,
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Remove a station from the driver's favourites."""

    driver_service.remove_favourite(db, driver_id, station_id)


# ---------------------------------------------------------------------------
# Compatibility
# ---------------------------------------------------------------------------


@router.get(
    "/compatible-stations",
    response_model=list[CompatibleStationOut],
)
def list_compatible_stations(
    vehicle_id: UUID | None = None,
    city: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    driver_id: UUID = Depends(get_driver_id),
    db: Session = Depends(get_db),
):
    """Find active stations compatible with a registered vehicle."""

    matches = driver_service.compatible_stations(
        db,
        driver_id,
        vehicle_id=vehicle_id,
        city=city,
        limit=limit,
    )

    results: list[CompatibleStationOut] = []

    for match in matches:
        station = StationOut.model_validate(match["station"])
        results.append(
            CompatibleStationOut(
                **station.model_dump(),
                compatible_charger_ids=match["compatible_charger_ids"],
                matched_connector_type=match["matched_connector_type"],
            )
        )

    return results
