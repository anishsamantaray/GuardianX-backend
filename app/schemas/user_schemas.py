from pydantic import BaseModel, EmailStr
from typing import List, Optional

class EmailRequest(BaseModel):
    email: EmailStr

class Address(BaseModel):
    line1: str
    line2: Optional[str] = ""
    city: str
    state: str
    lat: float
    long: float
    pincode : str

class UserSignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    whatsapp_opt_in: bool
    home_address: Address

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str