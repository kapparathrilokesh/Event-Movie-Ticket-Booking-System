from pathlib import Path

from fastapi.responses import FileResponse
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.event import Event
from app.models.screen import Screen
from app.models.seat import Seat
from app.models.seat_booking import SeatBooking
from app.models.showtime import Showtime
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse
from app.utils.email_service import send_email
from app.services.seat_lock_service import (
    acquire_seat_lock,
    release_seat_lock,
)
from app.services.qr_code_service import generate_ticket_qr
router = APIRouter(prefix="/bookings", tags=["Bookings"])

async def safely_release_seat_locks(
    showtime_id: int,
    seat_ids: list[int],
    user_id: int,
) -> None:
    """Release acquired locks without masking the original error."""
    for seat_id in seat_ids:
        try:
            await release_seat_lock(
                showtime_id,
                seat_id,
                user_id,
            )
        except Exception:
            # Locks will expire automatically after five minutes.
            pass



@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    booking_data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acquired_seats: list[int] = []

    user_id = current_user.id

    try:
        # 1. Verify the showtime exists.
        result = await db.execute(
            select(Showtime).where(
                Showtime.id == booking_data.showtime_id
            )
        )
        showtime = result.scalar_one_or_none()

        if showtime is None:
            raise HTTPException(
                status_code=404,
                detail="Showtime not found.",
            )

        if showtime.status != "Scheduled":
            raise HTTPException(
                status_code=400,
                detail="This showtime is not available for booking.",
            )

        # Handle both timezone-aware and naive database datetimes.
        now = datetime.now(
            showtime.starts_at.tzinfo
            if showtime.starts_at.tzinfo is not None
            else None
        )

        if showtime.starts_at <= now:
            raise HTTPException(
                status_code=400,
                detail="This showtime has already started.",
            )

        # 2. Verify the event is active.
        result = await db.execute(
            select(Event).where(Event.id == showtime.event_id)
        )
        event = result.scalar_one_or_none()

        if event is None or not event.is_active:
            raise HTTPException(
                status_code=400,
                detail="This event is not available for booking.",
            )

        if showtime.screen_id is None:
            raise HTTPException(
                status_code=400,
                detail="This showtime has no screen assigned.",
            )

        # 3. Verify the requested seats exist, are active,
        # and belong to this showtime's screen.
        result = await db.execute(
            select(Seat).where(
                Seat.id.in_(booking_data.seat_ids),
                Seat.screen_id == showtime.screen_id,
                Seat.is_active.is_(True),
            )
        )
        seats = result.scalars().all()

        if len(seats) != len(booking_data.seat_ids):
            raise HTTPException(
                status_code=400,
                detail=(
                    "One or more seats are inactive, invalid, "
                    "or do not belong to this showtime's screen."
                ),
            )

        # 4. Acquire a Redis lock for every requested seat.
        # If any seat is locked by another user, stop the booking.
        for seat_id in sorted(booking_data.seat_ids):
            locked = await acquire_seat_lock(
                showtime_id=showtime.id,
                seat_id=seat_id,
                user_id=user_id,
            )

            if not locked:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Seat {seat_id} is temporarily held "
                        "by another customer. Please try again."
                    ),
                )

            acquired_seats.append(seat_id)

        # 5. Check the permanent booking records in MySQL.
        result = await db.execute(
            select(SeatBooking.seat_id).where(
                SeatBooking.showtime_id == showtime.id,
                SeatBooking.seat_id.in_(booking_data.seat_ids),
            )
        )
        already_booked = result.scalars().all()

        if already_booked:
            raise HTTPException(
                status_code=409,
                detail=(
                    "One or more selected seats are already booked: "
                    f"{already_booked}"
                ),
            )

        # 6. Create the ticket and seat-booking records.
        quantity = len(seats)
        total_amount = showtime.base_price * quantity

        ticket = Ticket(
            booking_reference=secrets.token_hex(10).upper(),
            customer_id=user_id,
            showtime_id=showtime.id,
            quantity=quantity,
            total_amount=total_amount,
            status="Booked",
            payment_status="Pending",
        )

        db.add(ticket)
        await db.flush()

        # Generate a QR code for this ticket.
        qr_code_path = generate_ticket_qr(
            booking_reference=ticket.booking_reference,
            ticket_id=ticket.id,
        )

        ticket.qr_code_path = qr_code_path

        for seat_id in booking_data.seat_ids:
            db.add(
                SeatBooking(
                    ticket_id=ticket.id,
                    showtime_id=showtime.id,
                    seat_id=seat_id,
                    status="Booked",
                )
            )

        await db.commit()
        await db.refresh(ticket)

        response = BookingResponse.model_validate(ticket)

    except HTTPException:
        await db.rollback()

        await safely_release_seat_locks(
            booking_data.showtime_id,
            acquired_seats,
           user_id,
        )

        raise

    
    except IntegrityError:
        await db.rollback()

        await safely_release_seat_locks(
            booking_data.showtime_id,
            acquired_seats,
            user_id,
        )

        raise HTTPException(
            status_code=409,
            detail=(
                "A selected seat was booked by another request. "
                "Please refresh the seat map and try again."
            ),
        )


    
    
    except Exception:
        await db.rollback()

        await safely_release_seat_locks(
            booking_data.showtime_id,
            acquired_seats,
            user_id,
        )

        raise

    await safely_release_seat_locks(
        booking_data.showtime_id,
        acquired_seats,
        user_id,
    )

    # Send a booking confirmation notification after the booking commits.
    try:
        await send_email(
            recipient=current_user.email,
            subject="Booking Confirmation",
            body=(
                f"Hello {current_user.full_name},\n\n"
                "Your booking has been confirmed.\n"
                f"Booking Reference: {ticket.booking_reference}\n"
                f"Event: {event.title}\n"
                f"Quantity: {ticket.quantity}\n"
                f"Total Amount: Rs. {ticket.total_amount}\n"
                f"Payment Status: {ticket.payment_status}\n\n"
                "Thank you for booking with us!"
            ),
        )
    except Exception:
        # Email failures must not undo a successful booking.
        pass

    return response

@router.get(
    "/my-bookings",
    response_model=list[BookingResponse],
)
async def get_my_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):
    result = await db.execute(
        select(Ticket)
        .where(Ticket.customer_id == current_user.id)
        .order_by(Ticket.booked_at.desc())
    )

    bookings = result.scalars().all()

    return bookings

@router.get(
    "/{ticket_id}/qr-code",
    response_class=FileResponse,
)
async def get_ticket_qr_code(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found.",
        )

    if current_user.role != "Admin" and ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this ticket.",
        )

    if not ticket.qr_code_path:
        raise HTTPException(
            status_code=404,
            detail="QR code not found for this ticket.",
        )

    base_dir = Path(__file__).resolve().parents[2]
    qr_file = base_dir / ticket.qr_code_path

    if not qr_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="QR code image file does not exist.",
        )

    return FileResponse(
        path=str(qr_file),
        media_type="image/png",
        filename=qr_file.name,
    )

