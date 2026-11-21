from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

BOOKING_SLOT_MINUTES = 30
MAX_BOOKING_MINUTES = 240


class AvailableSlot(BaseModel):
    station_id: UUID
    charger_id: UUID
    charger_code: str
    charging_type: str
    connector_type: str
    power_kw: Decimal
    price_per_kwh: Decimal
    estimated_price: Decimal | None = None
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    timezone: str
    local_start: str
    local_end: str


class BookingProposalCreate(BaseModel):
    station_id: UUID
    charger_id: UUID
    start_at: datetime
    duration_minutes: int = Field(
        default=BOOKING_SLOT_MINUTES,
        ge=BOOKING_SLOT_MINUTES,
        le=MAX_BOOKING_MINUTES,
        multiple_of=BOOKING_SLOT_MINUTES,
    )
    vehicle_id: UUID | None = None
    connector_type: str | None = Field(default=None, max_length=50)


class BookingProposalOut(BaseModel):
    confirmation_id: UUID
    status: Literal["pending"] = "pending"
    expires_at: datetime | None = None
    summary: dict
    message: str = (
        "Review the booking summary and confirm explicitly to reserve."
    )


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_reference: str
    driver_id: UUID
    station_id: UUID
    charger_id: UUID
    vehicle_id: UUID | None
    connector_type: str
    start_at: datetime
    end_at: datetime
    status: str
    estimated_price: Decimal | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    station_name: str | None = None
    charger_code: str | None = None
    timezone: str | None = None
    local_start: str | None = None
    local_end: str | None = None


class ChargerAvailabilityOut(BaseModel):
    charger_id: UUID
    charger_code: str
    charging_type: str
    power_kw: Decimal
    price_per_kwh: Decimal
    status: str
    connector_types: list[str] = Field(default_factory=list)
    available_now: bool = False
    booked_until: datetime | None = None
    next_available_at: datetime | None = None


class StationAvailabilityOut(BaseModel):
    station_id: UUID
    station_name: str
    timezone: str
    as_of: datetime
    chargers: list[ChargerAvailabilityOut] = Field(default_factory=list)
