import redis.asyncio as aioredis
from typing import AsyncGenerator
import os
from app.config import settings
# replace this with actual redis url in production
REDIS_URL = settings.REDIS_URL


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()
