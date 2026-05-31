import redis.asyncio as aioredis
from typing import AsyncGenerator
import os

# replace this with actual redis url in production
REDIS_URL = os.environ.get('REDIS_URL', "redis://localhost:6379/0")


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    client = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()
