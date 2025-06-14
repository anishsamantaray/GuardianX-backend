from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EmergencyContact(BaseModel):
    name: str
    phone: str

class Address(BaseModel):
    line1: str
    line2: Optional[str] = ""
    city: str
    state: str

class UserSignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    whatsapp_opt_in: bool
    emergency_contacts: List[EmergencyContact]
    home_address: Address

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str