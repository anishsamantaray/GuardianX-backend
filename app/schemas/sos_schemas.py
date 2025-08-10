from pydantic import BaseModel,EmailStr



class SOSLocation(BaseModel):
    latitude: float
    longitude: float

class SOSTriggerRequest(BaseModel):
    email: EmailStr
    location: SOSLocation
    timestamp: str

class SOSHeartbeatRequest(BaseModel):
    email: EmailStr
    location: SOSLocation
    timestamp: str

class SOSEndRequest(BaseModel):
    email: EmailStr
    timestamp: str