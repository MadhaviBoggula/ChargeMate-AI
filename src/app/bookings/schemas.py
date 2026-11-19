from datetime import datetime
from pydantic import BaseModel


class BookingCreate(BaseModel):
    station_id: int
    booking_time: datetime


class BookingUpdate(BaseModel):
    booking_time: datetime
    status: str


class BookingResponse(BaseModel):
    id: int
    driver_id: int
    station_id: int
    booking_time: datetime
    status: str

    class Config:
        from_attributes = True