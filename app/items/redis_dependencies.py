from fastapi import Depends, HTTPException, status
import redis.asyncio as aioredis
from app.redis_config import get_redis
from app.items.security import get_current_user
from app.items.models import User
from app.config import settings
from abc import ABC, abstractmethod


MAX_REQUEST_PER_MIN = settings.MAX_REQUEST_PER_MIN
WINDOW_SECONDS = settings.WINDOW_SECONDS


class RateLimiter(ABC):

    @abstractmethod
    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:
        pass


class FixedWindowAlgo(RateLimiter):

    def __init__(self) -> None:
        pass

    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:

        # 1 create a unique string key using the authenticated user's ID
        redis_key = f"rate_limit:{user.id}"

        # 2 increment the counter atomatically
        current_count = await redis.incr(redis_key)

        # 3 if its a brand new key (count is 1), set its timer to live(ttl) to  60:
        if current_count == 1:
            await redis.expire(redis_key, WINDOW_SECONDS)

        # 4 check if they have breached the threshold
        if current_count > MAX_REQUEST_PER_MIN:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded via redis , please wait a minute."
            )

        # 5 pass the authenticated user forward to you view
        return user


fixed_window_obj = FixedWindowAlgo()


async def call_rate_limiter_algo(redis: aioredis.Redis = Depends(get_redis), user: User = Depends(get_current_user)):
    return await fixed_window_obj.is_allowed(redis=redis, user=user)
