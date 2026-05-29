from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.items.database import Base
from datetime import datetime, timedelta, timezone


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))


class RateCount(Base):
    __tablename__ = "ratecount"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    count: Mapped[int] = mapped_column(Integer)
    limit: Mapped[int] = mapped_column(Integer)
    last_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True))
