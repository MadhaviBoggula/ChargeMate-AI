from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    vehicle_number: str = Field(min_length=1, max_length=30)
    vehicle_model: str = Field(min_length=1, max_length=100)
    vehicle_type: str = Field(min_length=1, max_length=20)
    manufacturing_year: int = Field(ge=1900, le=2100)
    battery_capacity: int = Field(gt=0)
    connector_type: str = Field(min_length=1, max_length=50)


class VehicleUpdate(BaseModel):
    vehicle_number: str | None = Field(default=None, max_length=30)
    vehicle_model: str | None = Field(default=None, max_length=100)
    vehicle_type: str | None = Field(default=None, max_length=20)
    manufacturing_year: int | None = Field(default=None, ge=1900, le=2100)
    battery_capacity: int | None = Field(default=None, gt=0)
    connector_type: str | None = Field(default=None, max_length=50)


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vehicle_number: str
    vehicle_model: str
    vehicle_type: str
    manufacturing_year: int
    battery_capacity: int
    connector_type: str
    created_at: datetime


class FavoriteCreate(BaseModel):
    station_id: UUID


class FavoriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    station_id: UUID
    created_at: datetime
