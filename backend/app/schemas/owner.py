from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from uuid import UUID

class StationCreate(BaseModel):
    address_id: int
    name: str = Field(min_length=1, max_length=255)
    connectors: list[str] | None = None
    charger_type: str | None = Field(default=None, max_length=2)
    power: float = Field(gt=0)
    speed: str | None = None
    available_slots: int = Field(ge=0)
    total_slots: int = Field(ge=0)
    price_per_kwh: float = Field(ge=0)
    description: str = ""
    is_active: bool = True

    @model_validator(mode="after")
    def validate_slots(self):
        if self.available_slots > self.total_slots:
            raise ValueError(
                "available_slots cannot exceed total_slots"
            )
        return self


class StationUpdate(BaseModel):
    address_id: int | None = None
    name: str | None = None
    connectors: list[str] | None = None
    charger_type: str | None = None
    power: float | None = Field(default=None, gt=0)
    speed: str | None = None
    available_slots: int | None = Field(default=None, ge=0)
    total_slots: int | None = Field(default=None, ge=0)
    price_per_kwh: float | None = Field(default=None, ge=0)
    description: str | None = None
    is_active: bool | None = None


class StationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    address_id: int | None
    owner_id: UUID | None
    name: str
    location: str | None
    address: str | None
    connectors: list[str] | None
    charger_type: str | None
    power: float
    speed: str | None
    available_slots: int
    total_slots: int
    price_per_kwh: float
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ChargerCreate(BaseModel):
    station_id: UUID
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
    station_id: UUID
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
