import bcrypt
# imports for JWT
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.items.models import User
import jwt
from app.items.database import get_db


# tell passlib to handle bcrypt hashing


def hash_password(password: str) -> str:
    """Generate a secure , salted bcrypt hash string from plain text password."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies an incoming login password against the database record hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# configurations
SECRET_KEY = "key_FROM_ENV"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPRIE_MINUTES = 30

# Initialize security scheme
security = HTTPBearer()

# helper function


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))  # type:ignore
        if user_id == "None":
            raise credentials_exception
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise credentials_exception
