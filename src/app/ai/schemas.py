from datetime import datetime
from pydantic import BaseModel


class DemandForecastCreate(BaseModel):
    station_id: int
    forecast_date: str
    predicted_demand: float
    demand_level: str


class DemandForecastResponse(BaseModel):
    id: int
    station_id: int
    forecast_date: str
    predicted_demand: float
    demand_level: str
    created_at: datetime

    class Config:
        from_attributes = True