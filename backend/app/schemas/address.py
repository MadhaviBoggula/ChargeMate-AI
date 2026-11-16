from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class AddressCreate(BaseModel):
    hno: str | None = Field(default=None, max_length=50)
    street_village: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=4, max_length=10)
    lat: float | None = Field(default=None, ge=-90, le=90)
    long: float | None = Field(default=None, ge=-180, le=180)

class AddressUpdate(BaseModel):
    hno: str | None = None
    street_village: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    long: float | None = Field(default=None, ge=-180, le=180)

class AddressOut(AddressCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
