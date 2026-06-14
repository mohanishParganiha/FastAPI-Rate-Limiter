from fastapi import Depends, HTTPException, status
import redis.asyncio as aioredis
from redis.asyncio import WatchError
from app.redis_config import get_redis
from app.items.security import get_current_user
from app.items.models import User
from app.config import settings
from abc import ABC, abstractmethod
import time
from math import floor
from collections import deque

MAX_REQUEST_PER_MIN = settings.MAX_REQUEST_PER_MIN
WINDOW_SECONDS = settings.WINDOW_SECONDS


class RateLimiter(ABC):

    too_many_request_error_detail = "TOO MANY REQUESTS"

    @abstractmethod
    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:
        pass


class FixedWindowAlgo(RateLimiter):

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
                detail=self.too_many_request_error_detail
            )

        # 5 pass the authenticated user forward to you view
        return user


class TokenBucket(RateLimiter):

    def __init__(self) -> None:
        # 0 set some variables
        self.token_refill_rate = 0.1666
        self.max_tokens = float(MAX_REQUEST_PER_MIN)
        self.ttl = 300  # 5 minutes

    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:

        current_time = time.time()

        # 1 create a unique key using authenticated user's ID and value should be token limit and last_updated time
        redis_key = f"token_bucket:{user.id}"

        async with redis.pipeline(transaction=True) as pipe:
            try:
                # watch the key
                await pipe.watch(redis_key)

                # 2 get key data from redis server, you must use hgetall outside of transaction block watch -> execute
                key_data = await pipe.hgetall(redis_key)
                # use redis pipe line with transaction = true to initiate a transaction and avoid race condition

                # 3 check if key is empty
                if not key_data:  # if the key is empty this user is new user
                    tokens = self.max_tokens

                # 4 if key is not empty then calcualte toekns for existing user
                else:
                    token_need_to_fill = (
                        current_time - float(key_data['last_updated']))*self.token_refill_rate
                    tokens = min(self.max_tokens, float(
                        key_data['tokens'])+token_need_to_fill)

                # now check if user has token , reduce token if user has token then update redis key
                if tokens <= 1.0:
                    raise HTTPException(  # raise exception if user doesnot have tokens
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=self.too_many_request_error_detail
                    )

                # start the transaction
                pipe.multi()

                await pipe.hset(
                    name=redis_key,
                    mapping={
                        "tokens": tokens-1.0,
                        "last_updated": current_time
                    }
                )
                # set TTL for key expiration
                await pipe.expire(redis_key, self.ttl)

                # complete / commit the transaction
                await pipe.execute()

            except WatchError:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self.too_many_request_error_detail
                )

        return user


fixed_window_obj = FixedWindowAlgo()
token_bucket_obj = TokenBucket()


async def call_rate_limiter_algo(redis: aioredis.Redis = Depends(get_redis), user: User = Depends(get_current_user)):
    return await token_bucket_obj.is_allowed(redis=redis, user=user)
