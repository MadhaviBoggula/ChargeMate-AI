from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


# Create Scenario Request
class ScenarioCreate(BaseModel):

    name: str
    description: str
    initial_state: Dict[str, Any]
    current_state: Dict[str, Any]


# Update Scenario Request
class ScenarioUpdate(BaseModel):

    name: str
    description: str
    current_state: Dict[str, Any]


# Response Schema
class ScenarioResponse(BaseModel):

    id: int
    name: str
    description: str
    initial_state: Dict[str, Any]
    current_state: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True