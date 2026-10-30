
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.event import Event
from app.models.user import User
from app.models.venue import Venue
from app.schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter(prefix="/events", tags=["Events"])


def require_admin(user: User) -> None:
    if user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


def require_approved_organizer(user: User) -> None:
    if user.role == "Admin":
        return

    if user.role != "Organizer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organizer or Admin access required.",
        )

    if not user.is_active or not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your organizer account must be active and approved.",
        )


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_approved_organizer(current_user)

    result = await db.execute(
        select(Venue).where(
            Venue.id == event_data.venue_id,
            Venue.is_active.is_(True),
        )
    )
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active venue not found.",
        )

    event = Event(**event_data.model_dump())
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return event


@router.get("", response_model=list[EventResponse])
async def list_events(
    venue_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Event).join(Venue).where(
        Event.is_active.is_(True),
        Venue.is_active.is_(True),
    )

    if venue_id is not None:
        query = query.where(Event.venue_id == venue_id)

    query = query.order_by(Event.id.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Event)
        .join(Venue)
        .where(
            Event.id == event_id,
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

    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    updates = event_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if value is None and field in {
            "title", "event_type", "venue_id"
        }:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )

    if "venue_id" in updates and updates["venue_id"] is not None:
        result = await db.execute(
            select(Venue).where(
                Venue.id == updates["venue_id"],
                Venue.is_active.is_(True),
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active venue not found.",
            )

    for field, value in updates.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    event.is_active = False
    await db.commit()

    return None
