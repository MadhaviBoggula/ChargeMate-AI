

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BookingCreate(BaseModel):
    station_id: UUID
    booking_time: datetime
    duration_minutes: Literal[30, 60, 120]


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    station_id: UUID
    booking_time: datetime
    duration_minutes: int
    end_time: datetime
    status: str
    created_at: datetime


class BookingStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(Pending|Approved|Rejected|Completed|Cancelled)$"
    )
