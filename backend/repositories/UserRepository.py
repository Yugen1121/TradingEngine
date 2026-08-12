from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

class UserRepository():

    @staticmethod
    async def find_user_with_email(email: str, db: AsyncSession):
        result = await db.execute(select(User).where(User.email==email))
        result = result.scalar_one_or_none()
        return result

    @staticmethod
    async def create_user(email: str, password: str, db: AsyncSession) -> bool:
        try:
            new_user = User(email=email, password=password)
            db.add(new_user)
            print(new_user)
            await db.commit()
            return True
        except IntegrityError:
            await db.rollback()
            raise 

        except Exception as e:
            raise e
