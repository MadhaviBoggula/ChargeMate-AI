from pydantic import BaseModel


class StationCreate(BaseModel):
    station_name: str
    location: str
    latitude: float
    longitude: float
    total_connectors: int
    available_connectors: int
    charging_speed: str
    status: str


class StationUpdate(BaseModel):
    station_name: str
    location: str
    latitude: float
    longitude: float
    total_connectors: int
    available_connectors: int
    charging_speed: str
    status: str


class StationResponse(BaseModel):
    id: int
    station_name: str
    location: str
    latitude: float
    longitude: float
    total_connectors: int
    available_connectors: int
    charging_speed: str
    status: str

    class Config:
        from_attributes = True