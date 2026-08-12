"""
This file contains all the types
"""
from pydantic import BaseModel, Field


class Credentials(BaseModel):
    email: str = Field(..., min_length=8)
    password: str = Field(..., min_length=5)
