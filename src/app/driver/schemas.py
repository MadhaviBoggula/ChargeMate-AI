from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# ==========================
# Favorite Station Schemas
# ==========================

class FavoriteStationCreate(BaseModel):
    driver_id: int
    station_id: int


class FavoriteStationResponse(BaseModel):
    id: int
    driver_id: int
    station_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================
# Vehicle Schemas
# ==========================

class DriverVehicleCreate(BaseModel):
    driver_id: int
    vehicle_number: str
    vehicle_model: str
    vehicle_type: str
    manufacturing_year: int
    battery_capacity: int
    connector_type: str


class VehicleResponse(BaseModel):
    id: int
    vehicle_number: str
    vehicle_model: str
    vehicle_type: str
    manufacturing_year: int
    battery_capacity: int
    connector_type: str

    class Config:
        from_attributes = True


# ==========================
# Driver Schemas
# ==========================

class DriverCreate(BaseModel):
    full_name: str
    email: str
    phone: str


class DriverUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class DriverResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    created_at: datetime
    vehicles: List[VehicleResponse] = []

    class Config:
        from_attributes = True