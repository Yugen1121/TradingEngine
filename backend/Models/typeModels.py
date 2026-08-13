"""
This file contains all the types
"""
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from Models.model import OrderType, OrderStatus

class OrderSide(Enum):
    SELL = "sell"
    BUY = "buy"

class Credentials(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=5)

class TokenResponse(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field(default="bearer")


class Order(BaseModel):
    symbol: str = Field(...)
    quantity: int = Field(...)
    orderType: OrderType = Field(...)
    price: float = Field(..., min=1)
