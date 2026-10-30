
import asyncio
from redis.asyncio import Redis


async def main():
    redis_client = Redis.from_url(
        "redis://127.0.0.1:6379/0",
        decode_responses=True,
    )

    try:
        result = await redis_client.ping()
        print("ASYNC PING:", result)
        print("Async Redis connection successful!")
    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
