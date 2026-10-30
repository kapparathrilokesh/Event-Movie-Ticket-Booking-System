
import asyncio
import getpass

from sqlalchemy import select

from app.auth.security import hash_password
from app.database import AsyncSessionLocal
from app.models.user import User


async def main():
    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()
    password = getpass.getpass("Admin password: ")

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("A user with this email already exists.")
            print("No changes were made.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role="Admin",
            is_active=True,
            is_approved=True,
        )

        db.add(admin)
        await db.commit()

        print("Admin account created successfully.")
        print("Email:", email)
        print("Role:", admin.role)
        print("Approved:", admin.is_approved)


if __name__ == "__main__":
    asyncio.run(main())
