import asyncpg
import redis.asyncio as redis
from app.core.config import settings

from typing import Optional, AsyncGenerator

# Global connection pool
_pool: Optional[asyncpg.Pool] = None

# Postgres Database Connection Pool
async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=str(settings.database_url),
        min_size=settings.db_min_connections,
        max_size=settings.db_max_connections,
        command_timeout=1.5,
        timeout=0.5
    )


async def init_db():
    global _pool
    if _pool is None:
        try:
            _pool = await create_pool()
            print("Success: Connected to database!")
        except Exception as e:
            print(f"Error: Failed to connect to database: {e}")
            raise e
    else:
        print("Info: DB pool already initialized, skipping.")


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        raise RuntimeError("Error: DB pool not initialized.")
    return _pool


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn



# Redis Database Connection
_redis: Optional[redis.Redis] = None


async def init_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_connect_timeout=settings.redis_timeout,
                retry_on_timeout=True,
                max_connections=settings.redis_max_connections,
            )
            await _redis.ping()
            print("Success: Connected to Redis!")
        except Exception as e:
            print(f"Error: Failed to connect to Redis: {e}")
            raise e
    else:
        print("Info: Redis client already initialized, skipping.")


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        raise RuntimeError("Error: Redis client not initialized.")
    return _redis


async def ping_redis():
    r = await get_redis()
    await r.ping()
