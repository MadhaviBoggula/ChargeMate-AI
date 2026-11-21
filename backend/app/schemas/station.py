from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

ChargerStatus = Literal["active", "inactive", "maintenance", "faulted"]
ChargerAvailability = Literal["available", "occupied", "unavailable"]
ConnectorStatus = Literal["active", "inactive", "faulted"]
SessionStatus = Literal["active", "completed", "cancelled", "failed"]


class ConnectorCreate(BaseModel):
    connector_type: str = Field(min_length=1, max_length=50)
    power_kw: Decimal = Field(gt=0, le=1000)
    status: ConnectorStatus = "active"


class ConnectorUpdate(BaseModel):
    connector_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    power_kw: Decimal | None = Field(default=None, gt=0, le=1000)
    status: ConnectorStatus | None = None


class ConnectorOut(ConnectorCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    charger_id: UUID
    created_at: datetime
    updated_at: datetime


class ChargerCreate(BaseModel):
    charger_code: str = Field(min_length=1, max_length=80)
    charging_type: Literal["AC", "DC"]
    power_kw: Decimal = Field(gt=0, le=1000)
    status: ChargerStatus = "active"
    availability: ChargerAvailability = "available"
    price_per_kwh: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    connectors: list[ConnectorCreate] = Field(min_length=1)


class ChargerUpdate(BaseModel):
    charger_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
    )
    charging_type: Literal["AC", "DC"] | None = None
    power_kw: Decimal | None = Field(default=None, gt=0, le=1000)
    status: ChargerStatus | None = None
    availability: ChargerAvailability | None = None
    price_per_kwh: Decimal | None = Field(default=None, ge=0)
    connectors: list[ConnectorCreate] | None = Field(
        default=None,
        min_length=1,
    )


class ChargerStatusUpdate(BaseModel):
    status: ChargerStatus


class ChargerPriceUpdate(BaseModel):
    price_per_kwh: Decimal = Field(ge=0)


class ChargerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    station_id: UUID
    charger_code: str
    charging_type: str
    power_kw: Decimal
    status: str
    availability: str
    price_per_kwh: Decimal
    connectors: list[ConnectorOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class StationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=4, max_length=10)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    is_active: bool = True
    chargers: list[ChargerCreate] = Field(default_factory=list)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value


class StationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    pincode: str | None = Field(default=None, min_length=4, max_length=10)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str | None = Field(default=None, max_length=64)
    is_active: bool | None = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value


class StationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    address_line1: str | None
    address_line2: str | None
    city: str
    state: str
    pincode: str
    latitude: float | None
    longitude: float | None
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    connector_types: list[str] = Field(default_factory=list)
    min_price_per_kwh: Decimal | None = None
    max_power_kw: Decimal | None = None
    total_chargers: int = 0
    available_chargers: int = 0


class StationDetailOut(StationOut):
    chargers: list[ChargerOut] = Field(default_factory=list)


class ChargingSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    station_id: UUID
    charger_id: UUID
    driver_id: UUID | None
    booking_id: UUID | None
    started_at: datetime
    ended_at: datetime | None
    energy_kwh: Decimal
    duration_minutes: int
    price_per_kwh: Decimal
    revenue: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class RevenueSummary(BaseModel):
    station_id: UUID | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    session_count: int = 0
    total_energy_kwh: Decimal = Decimal("0.000")
    total_revenue: Decimal = Decimal("0.00")
    currency: str = "INR"


class StationAnalytics(BaseModel):
    station_id: UUID
    station_name: str
    session_count: int = 0
    total_energy_kwh: Decimal = Decimal("0.000")
    total_revenue: Decimal = Decimal("0.00")
    average_session_minutes: float = 0.0
    charger_count: int = 0
    utilization_percent: float = 0.0
    currency: str = "INR"


class OwnerAnalytics(BaseModel):
    start_at: datetime | None = None
    end_at: datetime | None = None
    station_count: int = 0
    charger_count: int = 0
    session_count: int = 0
    total_energy_kwh: Decimal = Decimal("0.000")
    total_revenue: Decimal = Decimal("0.00")
    average_revenue_per_station: Decimal = Decimal("0.00")
    stations: list[StationAnalytics] = Field(default_factory=list)
    currency: str = "INR"
