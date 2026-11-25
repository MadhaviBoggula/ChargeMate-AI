
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OwnerStationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    connectors: list[str] = Field(min_length=1)
    charger_type: str = Field(min_length=1, max_length=2)
    power: float = Field(gt=0)
    speed: str = Field(min_length=1, max_length=20)
    available_slots: int = Field(ge=0)
    total_slots: int = Field(ge=0)
    price_per_kwh: float = Field(ge=0)
    description: str = Field(max_length=1000)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_slots(self):
        if self.available_slots > self.total_slots:
            raise ValueError("Available slots cannot exceed total slots.")
        return self


class OwnerStationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    connectors: list[str] | None = Field(default=None, min_length=1)
    charger_type: str | None = Field(default=None, min_length=1, max_length=2)
    power: float | None = Field(default=None, gt=0)
    speed: str | None = Field(default=None, min_length=1, max_length=20)
    available_slots: int | None = Field(default=None, ge=0)
    total_slots: int | None = Field(default=None, ge=0)
    price_per_kwh: float | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool | None = None

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


class OwnerStationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    location: str
    address: str
    connectors: list[str]
    charger_type: str
    power: float
    speed: str
    available_slots: int
    total_slots: int
    price_per_kwh: float
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
