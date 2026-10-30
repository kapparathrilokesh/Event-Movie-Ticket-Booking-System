
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.venue import Venue
from app.models.screen import Screen
from app.schemas.screen import ScreenCreate, ScreenUpdate, ScreenResponse


router = APIRouter(prefix="/screens", tags=["Screens"])


def require_admin(user: User) -> None:
    if user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


@router.post(
    "",
    response_model=ScreenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_screen(
    screen_data: ScreenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Venue).where(
            Venue.id == screen_data.venue_id,
            Venue.is_active.is_(True),
        )
    )
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(status_code=404, detail="Active venue not found.")

    screen = Screen(
        venue_id=screen_data.venue_id,
        name=screen_data.name.strip(),
        total_seats=0,
    )
    db.add(screen)
    await db.commit()
    await db.refresh(screen)
    return screen


@router.get("", response_model=list[ScreenResponse])
async def list_screens(
    venue_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Screen).join(Venue).where(Venue.is_active.is_(True))

    if venue_id is not None:
        query = query.where(Screen.venue_id == venue_id)

    result = await db.execute(query.order_by(Screen.id))
    return result.scalars().all()


@router.get("/{screen_id}", response_model=ScreenResponse)
async def get_screen(
    screen_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Screen)
        .join(Venue)
        .where(
            Screen.id == screen_id,
            Venue.is_active.is_(True),
        )
    )
    screen = result.scalar_one_or_none()

    if screen is None:
        raise HTTPException(status_code=404, detail="Screen not found.")

    return screen


@router.patch("/{screen_id}", response_model=ScreenResponse)
async def update_screen(
    screen_id: int,
    screen_data: ScreenUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Screen).where(Screen.id == screen_id)
    )
    screen = result.scalar_one_or_none()

    if screen is None:
        raise HTTPException(status_code=404, detail="Screen not found.")

    updates = screen_data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(screen, field, value.strip() if isinstance(value, str) else value)

    await db.commit()
    await db.refresh(screen)
    return screen


@router.delete("/{screen_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_screen(
    screen_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Screen).where(Screen.id == screen_id)
    )
    screen = result.scalar_one_or_none()

    if screen is None:
        raise HTTPException(status_code=404, detail="Screen not found.")

    await db.delete(screen)
    await db.commit()
    return None
