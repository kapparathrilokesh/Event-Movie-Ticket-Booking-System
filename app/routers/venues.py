
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.venue import Venue
from app.schemas.venue import VenueCreate, VenueUpdate, VenueResponse


router = APIRouter(prefix="/venues", tags=["Venues"])


def require_admin_or_organizer(user: User) -> None:
    if user.role not in ("Admin", "Organizer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Organizer access required.",
        )

    if user.role == "Organizer" and not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organizer approval is required.",
        )


@router.post(
    "",
    response_model=VenueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_venue(
    venue_data: VenueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to create venues.",
        )

    venue = Venue(
        name=venue_data.name.strip(),
        address=venue_data.address.strip(),
        city=venue_data.city.strip(),
    )
    db.add(venue)
    await db.commit()
    await db.refresh(venue)
    return venue


@router.get("", response_model=list[VenueResponse])
async def list_venues(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Venue).where(Venue.is_active.is_(True)).order_by(Venue.id)
    )
    return result.scalars().all()


@router.get("/{venue_id}", response_model=VenueResponse)
async def get_venue(
    venue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Venue).where(
            Venue.id == venue_id,
            Venue.is_active.is_(True),
        )
    )
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found.")

    return venue


@router.patch("/{venue_id}", response_model=VenueResponse)
async def update_venue(
    venue_id: int,
    venue_data: VenueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to update venues.",
        )

    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found.")

    updates = venue_data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(venue, field, value.strip() if isinstance(value, str) else value)

    await db.commit()
    await db.refresh(venue)
    return venue


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_venue(
    venue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to deactivate venues.",
        )

    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(status_code=404, detail="Venue not found.")

    # Soft delete: preserve venue, screen, seat, and booking history.
    venue.is_active = False
    await db.commit()
    return None
