
import os

from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6379/0",
)

redis_client = Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


async def get_redis() -> Redis:
    """Return the shared asynchronous Redis client."""
    return redis_client


async def close_redis() -> None:
    """Close the Redis connection when the application shuts down."""
    await redis_client.aclose()
