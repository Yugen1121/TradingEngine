from Models.typeModels import Credentials, TokenResponse
from security.Authorization import Authorization
from services.auth import AuthenticationServices
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from database.models import get_db
import asyncio
import bcrypt

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(from_user: Credentials, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    email = from_user.email
    password = from_user.password
    try:
        result = await AuthenticationServices.authenticate_user(email, password, db)
        if result:
            token = Authorization.create_token(result)
            response = TokenResponse(access_token=token)
            return response
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
@router.post("/register")
async def register(from_user: Credentials, db: AsyncSession = Depends(get_db)):
    email = from_user.email
    password = from_user.password
    try:
        result = await AuthenticationServices.register_user(email=email, password=password, db=db)
        if result:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "message": "Account created successfully"
                }
            )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="An account with this code already exists"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )