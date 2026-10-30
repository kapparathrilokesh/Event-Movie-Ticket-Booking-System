
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.event import Event
from app.models.screen import Screen
from app.models.showtime import Showtime
from app.models.user import User
from app.models.venue import Venue
from app.schemas.showtime import (
    ShowtimeCreate,
    ShowtimeUpdate,
    ShowtimeResponse,
)

router = APIRouter(prefix="/showtimes", tags=["Showtimes"])


def require_admin(user: User) -> None:
    if user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


async def validate_screen(
    screen_id: int,
    db: AsyncSession,
) -> Screen:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screen not found in an active venue.",
        )

    return screen


@router.post(
    "",
    response_model=ShowtimeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_showtime(
    showtime_data: ShowtimeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Event).join(Venue).where(
            Event.id == showtime_data.event_id,
            Event.is_active.is_(True),
            Venue.is_active.is_(True),
        )
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active event not found.",
        )

    await validate_screen(showtime_data.screen_id, db)

    showtime = Showtime(**showtime_data.model_dump())
    db.add(showtime)
    await db.commit()
    await db.refresh(showtime)

    return showtime


@router.get("", response_model=list[ShowtimeResponse])
async def list_showtimes(
    event_id: int | None = None,
    screen_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Showtime)
        .join(Event, Showtime.event_id == Event.id)
        .join(Venue, Event.venue_id == Venue.id)
        .where(
            Event.is_active.is_(True),
            Venue.is_active.is_(True),
        )
    )

    if event_id is not None:
        query = query.where(Showtime.event_id == event_id)

    if screen_id is not None:
        query = query.where(Showtime.screen_id == screen_id)

    query = query.order_by(Showtime.starts_at)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{showtime_id}", response_model=ShowtimeResponse)
async def get_showtime(
    showtime_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Showtime)
        .join(Event, Showtime.event_id == Event.id)
        .join(Venue, Event.venue_id == Venue.id)
        .where(
            Showtime.id == showtime_id,
            Event.is_active.is_(True),
            Venue.is_active.is_(True),
        )
    )
    showtime = result.scalar_one_or_none()

    if showtime is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Showtime not found.",
        )

    return showtime


@router.patch("/{showtime_id}", response_model=ShowtimeResponse)
async def update_showtime(
    showtime_id: int,
    showtime_data: ShowtimeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Showtime).where(Showtime.id == showtime_id)
    )
    showtime = result.scalar_one_or_none()

    if showtime is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Showtime not found.",
        )

    updates = showtime_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if value is None and field in {
            "screen_id", "starts_at", "ends_at", "base_price", "status"
        }:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )

    new_start = updates.get("starts_at", showtime.starts_at)
    new_end = updates.get("ends_at", showtime.ends_at)

    if new_start is None or new_end is None or new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ends_at must be later than starts_at.",
        )

    if updates.get("screen_id") is not None:
        await validate_screen(updates["screen_id"], db)

    for field, value in updates.items():
        setattr(showtime, field, value)

    await db.commit()
    await db.refresh(showtime)

    return showtime


@router.delete(
    "/{showtime_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_showtime(
    showtime_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Showtime).where(Showtime.id == showtime_id)
    )
    showtime = result.scalar_one_or_none()

    if showtime is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Showtime not found.",
        )

    showtime.status = "Cancelled"
    await db.commit()

    return None
