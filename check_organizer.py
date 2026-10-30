
import asyncio
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                User.email == "organizer.test@example.com"
            )
        )
        user = result.scalar_one_or_none()

        print("Organizer found:", user is not None)

        if user:
            print("Role:", user.role)
            print("Approved:", user.is_approved)


asyncio.run(main())
