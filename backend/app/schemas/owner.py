from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class StationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    address_id: int
    description: str | None = None

class StationUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    address_id: int | None = None
    description: str | None = None

class StationOut(BaseModel):
    id: int
    owner_id: int
    name: str
    address_id: int
    description: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChargerCreate(BaseModel):
    station_id: int
    charger_code: str = Field(min_length=1, max_length=80)
    connector_type: str = Field(min_length=1, max_length=50)
    charging_type: str
    power_kw: Decimal = Field(gt=0, le=1000)
    status: str = "active"
    availability: str = "available"
    price_per_kwh: Decimal = Field(default=Decimal("0.00"), ge=0)

    @field_validator("charging_type")
    @classmethod
    def valid_charging_type(cls, v):
        v = v.upper()
        if v not in {"AC", "DC"}:
            raise ValueError("charging_type must be AC or DC")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v not in {"active", "inactive", "maintenance", "faulted"}:
            raise ValueError("Invalid charger status")
        return v

    @field_validator("availability")
    @classmethod
    def valid_availability(cls, v):
        if v not in {"available", "occupied", "unavailable"}:
            raise ValueError("Invalid availability")
        return v

class ChargerUpdate(BaseModel):
    connector_type: str | None = None
    charging_type: str | None = None
    power_kw: Decimal | None = Field(default=None, gt=0, le=1000)
    status: str | None = None
    availability: str | None = None
    price_per_kwh: Decimal | None = Field(default=None, ge=0)

class ChargerOut(BaseModel):
    id: int
    station_id: int
    charger_code: str
    connector_type: str
    charging_type: str
    power_kw: Decimal
    status: str
    availability: str
    price_per_kwh: Decimal
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
