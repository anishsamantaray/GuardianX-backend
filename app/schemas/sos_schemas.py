from pydantic import BaseModel
from typing import Optional

class SOSLocation(BaseModel):
    latitude: float
    longitude: float

class SOSTriggerRequest(BaseModel):
    location: SOSLocation
    timestamp: str  # ISO format recommended

class SOSHeartbeatRequest(BaseModel):
    location: SOSLocation
    timestamp: str
