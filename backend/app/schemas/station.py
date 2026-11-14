from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
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