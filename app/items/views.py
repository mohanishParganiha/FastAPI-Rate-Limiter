from fastapi import HTTPException, APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.items.database import get_db
from app.items.models import User
from app.items.schemas import CreateUser, UserResponse, UserLogin
from app.items.security import hash_password, verify_password

router = APIRouter(prefix='/api')


@router.post('/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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


@router.get('/users/{user_id}', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # get user from db
    result = await db.execute(select(User).where(User.id == user_id))
    # get db user from result
    db_user = result.scalars().first()  # type:ignore
    # check if user exsists
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="This user does not exist."
        )
    return db_user


@router.post('/users/login', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def login_user(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login view"""
    result = await db.execute(select(User).where(User.email == user_in.email))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Wrong Credentials")
    db_hashed_password = db_user.hashed_password
    if not verify_password(user_in.password.get_secret_value(), db_hashed_password):
        raise HTTPException(status_code=401, detail="Wrong Credentials")
    return db_user


# @router.post('/update-counter', status_code=200)
# async def update_counter(user: UpdateRate, db: AsyncSession = Depends(get_db)):
#     """Update counter """
#     result = await db.execute(select(User).where(User.email == user.email))
#     db_user = result.scalars().first()
#     if not db_user:
#         raise HTTPException(status_code=401, detail="wrong credentials")
#     if db_user.counter >= db_user.rate_limit:
#         raise HTTPException(status_code=249, detail="Too many request")
#     db_user.counter += 1
#     await db.commit()
#     await db.refresh(db_user)
#     return {
#         "status": "success",
#         "current_counter": db_user.counter,
#         "max_allowed": db_user.rate_limit
#     }
