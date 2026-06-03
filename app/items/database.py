from typing import Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os
from app.config import settings

# Using the asyncpg driver for high-performance async connections
DATABASE_URL = settings.DATABASE_URL

# 1. Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# 2. Create a session maker for handling transactions
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# 3. Create a Base class that models will inherit from (like Django's models.Model)
class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session
