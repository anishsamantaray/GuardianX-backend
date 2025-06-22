from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class Location(BaseModel):
    latitude: float
    longitude: float

class IncidentReport(BaseModel):
    email: EmailStr
    incident_type: str = Field(...)
    description: Optional[str] = ""
    location: Location
    timestamp: datetime
