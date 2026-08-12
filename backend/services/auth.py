"""
This file contains everything related to authentication
"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from repositories.UserRepository import UserRepository
import asyncio
import bcrypt
from sqlalchemy.exc import IntegrityError

class AuthenticationServices():

    @staticmethod
    async def authenticate_user(email: str, password: str, db: AsyncSession):
        user: User = await UserRepository.find_user_with_email(email, db)
        if not user:
            raise ValueError("Invalid credentials")

        valid = await asyncio.to_thread(
            bcrypt.checkpw,
            password.encode('utf-8'),
            user.password,
            )
        if valid:
            return user.id
        raise ValueError("Invalid credentials")

    @staticmethod
    async def register_user(email: str, password: str, db: AsyncSession) -> bool:
        password = await asyncio.to_thread(bcrypt.hashpw, 
                                           password.encode('utf-8'),
                                           bcrypt.gensalt()
                                           )
        result = await UserRepository.create_user(email=email, password=password, db=db)
        if result:
            return True
    