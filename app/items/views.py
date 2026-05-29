from datetime import timedelta, datetime, timezone

from fastapi import HTTPException, APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.items.database import get_db
from app.items.models import User, RateCount
from app.items.schemas import CreateUser, UserResponse, UserLogin, Token, RateCountResponse
from app.items.security import hash_password, verify_password, get_current_user, create_access_token, ACCESS_TOKEN_EXPRIE_MINUTES

public_router = APIRouter(prefix='/users')


@public_router.post('/create/', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: CreateUser, db: AsyncSession = Depends(get_db)):
    # 1. pydantic has already validated password and other fields through CreateUser schema

    # 2. check if user exists using sqlalchemy
    result = await db.execute(select(User).where(User.email == user_in.email))
    db_user = result.scalars().first()  # type: ignore
    if db_user:
        raise HTTPException(
            status_code=400,
            detail='Email already registered'
        )

    # 3. hash the password and create the database object
    fake_hashed_password = hash_password(user_in.password.get_secret_value())
    new_db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=fake_hashed_password
    )

    # 4. save to db.
    db.add(new_db_user)
    await db.commit()
    await db.refresh(new_db_user)
    return new_db_user


@public_router.post('/login/', response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login view"""
    result = await db.execute(select(User).where(User.email == user_in.email))
    db_user = result.scalars().first()
    if not db_user or not verify_password(user_in.password.get_secret_value(), db_user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Incorrect username or password")

    # generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPRIE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


authenticated_router = APIRouter(
    prefix="/users", dependencies=[Depends(get_current_user)])


@authenticated_router.get('/users/get-user', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, user: User = Depends(get_current_user)):
    # check if user exsists
    return user


TIME_WINDOW_SIZE = 1  # 1 minute


@authenticated_router.post('/update/count', response_model=RateCountResponse)
async def update_count(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RateCount).where(RateCount.id == user.id))
    user_rate_obj = result.scalars().first()

    now = datetime.now(timezone.utc)
    if user_rate_obj:
        if now <= user_rate_obj.last_reset_at + timedelta(minutes=TIME_WINDOW_SIZE):
            if user_rate_obj.count + 1 > user_rate_obj.limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests"
                )
            user_rate_obj.count += 1
        else:
            user_rate_obj.last_reset_at = now
            user_rate_obj.count = 1

    else:
        user_rate_obj = RateCount(
            id=user.id,
            count=1,
            limit=5,
            last_reset_at=now
        )
        db.add(user_rate_obj)
    await db.commit()
    await db.refresh(user_rate_obj)
    return user_rate_obj
