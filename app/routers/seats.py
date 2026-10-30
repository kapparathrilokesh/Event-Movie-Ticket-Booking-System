
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.venue import Venue
from app.models.screen import Screen
from app.models.seat import Seat
from app.schemas.seat import SeatCreate, SeatUpdate, SeatResponse


router = APIRouter(prefix="/seats", tags=["Seats"])


def require_admin(user: User) -> None:
    if user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


@router.post(
    "",
    response_model=SeatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_seat(
    seat_data: SeatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Screen)
        .join(Venue)
        .where(
            Screen.id == seat_data.screen_id,
            Venue.is_active.is_(True),
        )
    )
    screen = result.scalar_one_or_none()

    if screen is None:
        raise HTTPException(
            status_code=404,
            detail="Screen not found in an active venue.",
        )

    seat = Seat(
        screen_id=seat_data.screen_id,
        row_label=seat_data.row_label.strip().upper(),
        seat_number=seat_data.seat_number,
        category=seat_data.category.strip(),
    )

    db.add(seat)

    try:
        await db.commit()
        await db.refresh(seat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This seat position already exists in the screen.",
        )

    # Keep the screen's total_seats field synchronized.
    result = await db.execute(
        select(Seat.id).where(
            Seat.screen_id == screen.id,
            Seat.is_active.is_(True),
        )
    )
    screen.total_seats = len(result.scalars().all())
    await db.commit()

    return seat


@router.get("", response_model=list[SeatResponse])
async def list_seats(
    screen_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Seat)
        .join(Screen)
        .join(Venue)
        .where(Venue.is_active.is_(True), Seat.is_active.is_(True))
    )

    if screen_id is not None:
        query = query.where(Seat.screen_id == screen_id)

    result = await db.execute(
        query.order_by(Seat.screen_id, Seat.row_label, Seat.seat_number)
    )
    return result.scalars().all()


@router.get("/{seat_id}", response_model=SeatResponse)
async def get_seat(
    seat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Seat)
        .join(Screen)
        .join(Venue)
        .where(
            Seat.id == seat_id,
            Seat.is_active.is_(True),
            Venue.is_active.is_(True),
        )
    )
    seat = result.scalar_one_or_none()

    if seat is None:
        raise HTTPException(status_code=404, detail="Seat not found.")

    return seat


@router.patch("/{seat_id}", response_model=SeatResponse)
async def update_seat(
    seat_id: int,
    seat_data: SeatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Seat).where(Seat.id == seat_id)
    )
    seat = result.scalar_one_or_none()

    if seat is None:
        raise HTTPException(status_code=404, detail="Seat not found.")

    updates = seat_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
            if field == "row_label":
                value = value.upper()
        setattr(seat, field, value)

    try:
        await db.commit()
        await db.refresh(seat)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This seat position already exists in the screen.",
        )

    return seat


@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_seat(
    seat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Seat).where(Seat.id == seat_id)
    )
    seat = result.scalar_one_or_none()

    if seat is None:
        raise HTTPException(status_code=404, detail="Seat not found.")

    seat.is_active = False

    result = await db.execute(
        select(Seat.id).where(
            Seat.screen_id == seat.screen_id,
            Seat.is_active.is_(True),
        )
    )
    active_count = len(result.scalars().all())

    screen_result = await db.execute(
        select(Screen).where(Screen.id == seat.screen_id)
    )
    screen = screen_result.scalar_one_or_none()

    if screen is not None:
        screen.total_seats = active_count

    await db.commit()
    return None
