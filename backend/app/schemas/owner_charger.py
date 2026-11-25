from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


ChargerStatus = Literal["active", "inactive", "maintenance", "faulted"]
ChargerAvailability = Literal["available", "occupied", "unavailable"]
ChargingType = Literal["AC", "DC"]


class OwnerChargerCreate(BaseModel):
    station_id: UUID
    charger_code: str = Field(min_length=1, max_length=80)
    connector_type: str = Field(min_length=1, max_length=50)
    charging_type: ChargingType
    power_kw: Decimal = Field(gt=0, le=1000)
    status: ChargerStatus = "active"
    availability: ChargerAvailability = "available"
    price_per_kwh: Decimal = Field(default=Decimal("0.00"), ge=0)

    @field_validator("charging_type", mode="before")
    @classmethod
    def normalize_charging_type(cls, value):
        if isinstance(value, str):
            return value.upper()
        return value


class OwnerChargerUpdate(BaseModel):
    connector_type: str | None = Field(default=None, min_length=1, max_length=50)
    charging_type: ChargingType | None = None
    power_kw: Decimal | None = Field(default=None, gt=0, le=1000)
    status: ChargerStatus | None = None
    availability: ChargerAvailability | None = None
    price_per_kwh: Decimal | None = Field(default=None, ge=0)

    @field_validator("charging_type", mode="before")
    @classmethod
    def normalize_charging_type(cls, value):
        if isinstance(value, str):
            return value.upper()
        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")

        if any(
            getattr(self, field_name) is None
            for field_name in self.model_fields_set
        ):
            raise ValueError("Updated fields cannot be null.")

        return self


class OwnerChargerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
