"""
This file contains all the types
"""
from pydantic import BaseModel, Field, EmailStr


class Credentials(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=5)

class TokenResponse(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field(default="bearer")