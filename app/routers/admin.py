
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.security import hash_password
from app.database import get_db
from app.models.user import User


router = APIRouter(prefix="/admin", tags=["Admin"])


class StaffCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, min_length=10, max_length=10)
    venue_id: int | None = Field(default=None, gt=0)


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


@router.put("/organizers/{user_id}/approve")
async def approve_organizer(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    organizer = result.scalar_one_or_none()

    if organizer is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if organizer.role != "Organizer":
        raise HTTPException(
            status_code=400,
            detail="This user is not an organizer.",
        )

    if organizer.is_approved:
        return {
            "message": "Organizer is already approved.",
            "user_id": organizer.id,
            "is_approved": organizer.is_approved,
        }

    organizer.is_approved = True
    await db.commit()
    await db.refresh(organizer)

    return {
        "message": "Organizer approved successfully.",
        "user_id": organizer.id,
        "full_name": organizer.full_name,
        "is_approved": organizer.is_approved,
    }


@router.post("/staff", status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    email = str(staff_data.email).strip().lower()

    result = await db.execute(
        select(User).where(User.email == email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    if staff_data.phone:
        result = await db.execute(
            select(User).where(User.phone == staff_data.phone)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this phone number already exists.",
            )

    staff = User(
        full_name=staff_data.full_name.strip(),
        email=email,
        phone=staff_data.phone,
        hashed_password=hash_password(staff_data.password),
        role="Staff",
        is_active=True,
        is_approved=True,
    )

    db.add(staff)
    await db.commit()
    await db.refresh(staff)

    return {
        "message": "Staff account created successfully.",
        "id": staff.id,
        "full_name": staff.full_name,
        "email": staff.email,
        "role": staff.role,
        "is_active": staff.is_active,
        "is_approved": staff.is_approved,
    }
