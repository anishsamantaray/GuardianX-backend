from pydantic import BaseModel, EmailStr
from typing import Literal


class AllyRequestInput(BaseModel):
    to_email: EmailStr


class AllyResponseInput(BaseModel):
    from_email: EmailStr
    response: Literal["accepted", "rejected"]