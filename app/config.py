import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Secret keys
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "fallback-secret-for-dev")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", '')
    REDIS_URL: str = os.environ.get("REDIS_URL", '')

    # JWT settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPRIE_MINUTES: int = 30

    # Rate Limiter settings
    MAX_REQUEST_PER_MIN: int = 10
    WINDOW_SECONDS: int = 60

    # CORS Configuration (Define your allowed origins here)
    # Use a string or a list. For development, you can use ["*"]
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://vercel.app"  # Your future Vercel URL
    ]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Filters out Docker database variables
    }


# Create a single instance to import across your app
settings = Settings()
