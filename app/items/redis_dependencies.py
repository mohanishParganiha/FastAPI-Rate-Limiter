from fastapi import Depends, HTTPException, status
import redis.asyncio as aioredis
from redis.asyncio import WatchError
from app.redis_config import get_redis
from app.items.security import get_current_user
from app.items.models import User
from app.config import settings
from abc import ABC, abstractmethod
import time

MAX_REQUEST_PER_MIN = settings.MAX_REQUEST_PER_MIN
WINDOW_SECONDS = settings.WINDOW_SECONDS


class RateLimiter(ABC):

    too_many_request_error_detail = "TOO MANY REQUESTS"

    @abstractmethod
    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:
        pass


class FixedWindowAlgo(RateLimiter):

    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:

        # 1create a unique key using the authenticated user's ID
        redis_key = f"rate_limit:{user.id}"

        # 2increment the counter atomatically
        current_count = await redis.incr(redis_key)

        # 3if its a brand new key (count is 1), set its ttl to 60:
        if current_count == 1:
            await redis.expire(redis_key, WINDOW_SECONDS)

        # 4check if they have breached the threshold
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
        self.refil_rate = 0.1666
        self.max_tokens = float(MAX_REQUEST_PER_MIN)
        self.ttl = 300  # 5 minutes

    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:

        current_time = time.time()

        """1 create a unique key using authenticated user's ID and
        value should be token limit and last_updated time"""
        redis_key = f"token_bucket:{user.id}"

        async with redis.pipeline(transaction=True) as pipe:
            try:
                # watch the key
                await pipe.watch(redis_key)

                """2 get key data from redis server, you must use hgetall
                outside of transaction block watch -> execute"""
                key_data = await pipe.hgetall(redis_key)
                """use redis pipe line with transaction = true to initiate a
                transaction and avoid race condition"""

                # 3 check if key is empty
                if not key_data:  # if the key is empty this user is new user
                    tokens = self.max_tokens

                # 4 if key is not empty then calcualte toekns for existing user
                else:
                    token_need_to_fill = (
                        current_time -
                        float(key_data['last_updated']))*self.refil_rate
                    tokens = min(self.max_tokens, float(
                        key_data['tokens'])+token_need_to_fill)

                """now check if user has token ,
                reduce token if user has token then update redis key"""
                if tokens <= 1.0:
                    # raise exception if user doesnot have tokens
                    raise HTTPException(
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


class LeakyBucket(RateLimiter):

    def __init__(self) -> None:
        self.LEAKY_BUCKET_SIZE = 10.0
        self.LEAKING_FLOW_RATE = 0.5
        self.ttl = 60

    async def is_allowed(self, redis: aioredis.Redis, user: User) -> User:
        now = time.time()
        redis_key = f"leaky_bucket:{user.id}"

        """Use an async transaction pipeline with WATCH to
        prevent race conditions"""
        async with redis.pipeline(transaction=True) as pipe:
            try:
                # Watch the key for changes made by other concurrent requests
                await pipe.watch(redis_key)

                # Fetch existing data safely
                key_data = await pipe.hgetall(redis_key)

                if not key_data:
                    tokens = 0.0
                else:
                    """Note: Redis decodes bytes; ensure
                    keys are strings or decode them"""
                    last_leak = float(key_data.get(
                        b'last_leak_time',
                        key_data.get('last_leak_time', now)))
                    current_tokens = float(key_data.get(
                        b'tokens_in_bucket',
                        key_data.get('tokens_in_bucket', 0.0)))

                    time_elapsed = now - last_leak
                    tokens_left = current_tokens - \
                        (time_elapsed * self.LEAKING_FLOW_RATE)
                    tokens = max(tokens_left, 0.0)

                # 2. Check capacity constraints
                if tokens >= self.LEAKY_BUCKET_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=self.too_many_request_error_detail
                    )

                # 3. Queue atomic write operations
                pipe.multi()
                pipe.hset(
                    name=redis_key,
                    mapping={
                        'tokens_in_bucket': tokens + 1.0,
                        'last_leak_time': now
                    }
                )
                pipe.expire(redis_key, self.ttl)

                # Execute the transaction
                await pipe.execute()

            except WatchError:
                """Another concurrent request modified the key
                during our execution!
                Instead of letting it pass,
                safely treat it as a temporary failure/conflict"""
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=self.too_many_request_error_detail
                )

        return user


# create objects
fixed_window_obj = FixedWindowAlgo()
token_bucket_obj = TokenBucket()
leaky_bucket_obj = LeakyBucket()


async def call_rate_limiter_algo(
        redis: aioredis.Redis = Depends(get_redis),
        user: User = Depends(get_current_user)):
    return await leaky_bucket_obj.is_allowed(redis=redis, user=user)
