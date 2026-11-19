from pydantic import BaseModel
from datetime import datetime


class RecommendationCreate(BaseModel):
    station_id: int
    recommendation_type: str
    message: str
    priority: str
    confidence: float


class RecommendationResponse(BaseModel):
    id: int
    station_id: int
    recommendation_type: str
    message: str
    priority: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True