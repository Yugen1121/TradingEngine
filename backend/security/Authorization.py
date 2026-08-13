"""
This file contains anythig related to authorization
"""
import os
import jwt
from jwt import InvalidTokenError
from datetime import time, timedelta, datetime, timezone

TIME_DELTA = 7
ALGORITHM = "HS256"
JWT_SECRET = "qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"

class Authorization():
    """
    Responsible for jwt createion, authentication
    """
    @staticmethod
    def check_token(token) -> None | str:
        try:
            info = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[ALGORITHM]
                )

            user_id = info.get('sub')
            if user_id is None:
                return None
            return user_id
        except InvalidTokenError:
            return None

    @staticmethod
    def create_token(user_id: int) -> str:
        expire_time = datetime.now(timezone.utc) + timedelta(days=TIME_DELTA) 

        to_encode = {
            "sub": str(user_id),
            "exp": expire_time
        }

        encoded_jwt = jwt.encode(
            to_encode,
            JWT_SECRET,
            algorithm=ALGORITHM
        )
        return encoded_jwt
