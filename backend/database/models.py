"""
This files dontains the databaseModels
"""
import asyncio
import enum
from sqlalchemy import ForeignKey, Enum, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

class Base(DeclarativeBase):
    pass

class OrderAction(str, enum.Enum):
    SELL = "sell"
    BUY = "buy"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column()

    orders = relationship("Order", back_populates="owner")
    owned = relationship("OwnedStock", back_populates="owner")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    ownerId: Mapped[int] = mapped_column(ForeignKey("users.id"), )
    stock: Mapped[str] = mapped_column(ForeignKey("stocks.name"))
    Ordertype: Mapped[str] =  mapped_column(ForeignKey("tradeTypes.type"))
    orderaction: Mapped[OrderAction] = mapped_column(Enum(OrderAction))
    quantity: Mapped[int] = mapped_column(nullable=False)
    owner = relationship("User", back_populates="orders")
    

class Stock(Base):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(unique=True, primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    initial_listing: Mapped[float] = mapped_column(nullable=False)

class TradeType(Base):
    __tablename__ = "tradeTypes"

    type: Mapped[str] = mapped_column(unique=True, primary_key=True)

class OwnedStock(Base):
    __tablename__ = "ownedStocks"

    ownerId: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    stock: Mapped[str] = mapped_column(ForeignKey("stocks.name"), primary_key=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    owner = relationship("User", back_populates="owned")

engine = create_async_engine("sqlite+aiosqlite:///database.sqlite", echo=True)

Session = async_sessionmaker(
    bind=engine, 
    expire_on_commit=True
    )                         

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Session() as session:
        yield session

if __name__ == "__main__":
    asyncio.run(init_db())