from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.station import StationOut


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=1, max_length=32)
    nickname: str | None = Field(default=None, max_length=80)
    vehicle_model: str | None = Field(default=None, max_length=120)
    vehicle_type: str = Field(default="car", min_length=1, max_length=50)
    manufacturing_year: int | None = Field(
        default=None,
        ge=1950,
        le=2100,
    )
    battery_capacity_kwh: Decimal | None = Field(
        default=None,
        gt=0,
        le=1000,
    )
    connector_type: str = Field(min_length=1, max_length=50)
    is_primary: bool = False


class VehicleUpdate(BaseModel):
    registration_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
    )
    nickname: str | None = Field(default=None, max_length=80)
    vehicle_model: str | None = Field(default=None, max_length=120)
    vehicle_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    manufacturing_year: int | None = Field(
        default=None,
        ge=1950,
        le=2100,
    )
    battery_capacity_kwh: Decimal | None = Field(
        default=None,
        gt=0,
        le=1000,
    )
    connector_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    is_primary: bool | None = None


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    driver_id: UUID
    registration_number: str
    nickname: str | None
    vehicle_model: str | None
    vehicle_type: str
    manufacturing_year: int | None
    battery_capacity_kwh: Decimal | None
    connector_type: str
    is_primary: bool


class DriverPreferenceUpdate(BaseModel):
    preferred_connector_type: str | None = Field(
        default=None,
        max_length=50,
    )
    preferred_charging_type: Literal["AC", "DC"] | None = None
    max_price_per_kwh: Decimal | None = Field(default=None, ge=0)
    preferred_city: str | None = Field(default=None, max_length=100)
    default_vehicle_id: UUID | None = None


class DriverPreferenceOut(BaseModel):
    driver_id: UUID
    preferred_connector_type: str | None = None
    preferred_charging_type: str | None = None
    max_price_per_kwh: Decimal | None = None
    preferred_city: str | None = None
    default_vehicle_id: UUID | None = None


class FavouriteStationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    station_id: UUID
    station: StationOut
    created_at: datetime


class CompatibleStationOut(StationOut):
    compatible_charger_ids: list[UUID] = Field(default_factory=list)
    matched_connector_type: str | None = None
