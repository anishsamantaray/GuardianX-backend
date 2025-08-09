from pydantic import BaseModel, EmailStr
from typing import Literal
class AllyRequestInput(BaseModel):
    from_email: EmailStr
    to_email: EmailStr

class AllyResponseInput(BaseModel):
    from_email: EmailStr
    to_email: EmailStr
    response: Literal["accepted", "rejected"]