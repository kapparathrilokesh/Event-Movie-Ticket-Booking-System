
import asyncio

from sqlalchemy import text

from app.database import engine


async def test_connection():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT DATABASE()"))
            database_name = result.scalar_one()

            print(f"Database connected successfully: {database_name}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
