
import asyncio

from app.services.redis_client import get_redis, close_redis


async def main():
    client = await get_redis()

    try:
        result = await client.ping()
        print("Redis module PING:", result)
        print("Redis module test successful!")
    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
