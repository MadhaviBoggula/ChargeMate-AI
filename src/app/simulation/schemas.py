from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


# Create Scenario Request
class ScenarioCreate(BaseModel):

    name: str
    description: str
    initial_state: Dict[str, Any]
    current_state: Dict[str, Any]
    status: str = "Created"


# Update Scenario Request
class ScenarioUpdate(BaseModel):

    name: str
    description: str
    current_state: Dict[str, Any]
    status: str


# Response Schema
class ScenarioResponse(BaseModel):

    id: int
    name: str
    description: str
    initial_state: Dict[str, Any]
    current_state: Dict[str, Any]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True