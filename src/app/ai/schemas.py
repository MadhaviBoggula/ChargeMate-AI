from pydantic import BaseModel
from datetime import datetime


# ---------------------------------
# Demand Forecast Schemas
# ---------------------------------

class DemandForecastCreate(BaseModel):
    station_id: int
    forecast_date: str
    predicted_demand: float
    demand_level: str


class DemandForecastResponse(DemandForecastCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------
# Fault Detection Schemas
# ---------------------------------

class FaultDetectionCreate(BaseModel):
    station_id: int
    connector_id: int
    fault_type: str
    severity: str
    confidence: float


class FaultDetectionResponse(FaultDetectionCreate):
    id: int
    detected_at: datetime

    class Config:
        from_attributes = True