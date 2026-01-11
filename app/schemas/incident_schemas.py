from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Location(BaseModel):
    latitude: float
    longitude: float


class IncidentReport(BaseModel):
    incident_type: str = Field(...)
    description: Optional[str] = ""
    location: Location
    timestamp: datetime
