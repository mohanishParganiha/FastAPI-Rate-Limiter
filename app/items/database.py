from typing import Optional, Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Using the asyncpg driver for high-performance async connections
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Set DATABASE_URL to a valid SQLAlchemy URL before starting the app."
    )

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
