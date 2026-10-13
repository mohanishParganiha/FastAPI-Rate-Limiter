from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.items.database import get_db
from app.items.models import User
from app.items.redis_dependencies import call_rate_limiter_algo
from app.items.schemas import CreateUser, Token, UserLogin, UserResponse
from app.items.security import (
    ACCESS_TOKEN_EXPRIE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

public_router = APIRouter(prefix="/users")


@public_router.post(
    "/create/", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_in: CreateUser, db: Annotated[AsyncSession, Depends(get_db)]
):
    # pydantic has already validated password and
    # other fields through CreateUser schema

    # check if user exists using sqlalchemy
    result = await db.execute(select(User).where(User.email == user_in.email))
    db_user = result.scalars().first()  # type: ignore
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # hash the password and create the database object
    fake_hashed_password = hash_password(user_in.password.get_secret_value())
    new_db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=fake_hashed_password,
    )

    # save to db.
    db.add(new_db_user)
    await db.commit()
    await db.refresh(new_db_user)
    return new_db_user


@public_router.post("/login/", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(user_in: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]):
    """Login view"""
    result = await db.execute(select(User).where(User.email == user_in.email))
    db_user = result.scalars().first()
    if not db_user or not verify_password(
        user_in.password.get_secret_value(), db_user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPRIE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


authenticated_router = APIRouter(prefix="/users")


@authenticated_router.get(
    "/users/get-user", response_model=UserResponse, status_code=status.HTTP_200_OK
)
def get_user(user_id: int, user: Annotated[User, Depends(get_current_user)]):
    # check if user exsists
    return user


@authenticated_router.post(
    "/update/count",
)
def check_rate_limiter(user: Annotated[User, Depends(call_rate_limiter_algo)]):
    return {
        "status": "Success",
        "user_id": user.id,
        "message": "hello from lightning fast redis rate limiter!",
    }
