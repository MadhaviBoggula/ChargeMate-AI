from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ==========================
# Favorite Station Schemas
# ==========================

class FavoriteStationCreate(BaseModel):
    driver_id: int = Field(..., gt=0)
    station_id: int = Field(..., gt=0)


class FavoriteStationResponse(BaseModel):
    id: int
    driver_id: int
    station_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# ==========================
# Vehicle Schemas
# ==========================

class DriverVehicleCreate(BaseModel):
    driver_id: int = Field(..., gt=0)
    vehicle_number: str = Field(..., min_length=1, max_length=20)
    vehicle_model: str = Field(..., min_length=2, max_length=100)
    vehicle_type: str = Field(..., min_length=2, max_length=50)
    manufacturing_year: int = Field(..., ge=1900)
    battery_capacity: int = Field(..., gt=0)
    connector_type: str = Field(..., min_length=2, max_length=50)


class VehicleResponse(BaseModel):
    id: int
    vehicle_number: str
    vehicle_model: str
    vehicle_type: str
    manufacturing_year: int
    battery_capacity: int
    connector_type: str

    model_config = {
        "from_attributes": True
    }


# ==========================
# Driver Schemas
# ==========================

class DriverCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)


class DriverUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)


class DriverResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str
    created_at: datetime
    vehicles: List[VehicleResponse] = []

    model_config = {
        "from_attributes": True
    }