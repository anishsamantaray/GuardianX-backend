from pydantic import BaseModel
from datetime import datetime


class SOSLocation(BaseModel):
    latitude: float
    longitude: float


class SOSTriggerRequest(BaseModel):
    location: SOSLocation
    timestamp: datetime


class SOSHeartbeatRequest(BaseModel):
    location: SOSLocation
    timestamp: datetime


class SOSEndRequest(BaseModel):
    timestamp: datetime
