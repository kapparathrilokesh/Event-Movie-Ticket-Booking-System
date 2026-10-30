
import secrets
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.payment import Payment
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate,
    PaymentProcess,
    PaymentResponse,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify that the ticket exists and belongs to the logged-in user.
    result = await db.execute(
        select(Ticket)
        .where(
            Ticket.id == payment_data.ticket_id,
            Ticket.customer_id == current_user.id,
        )
        .with_for_update()
    )
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    if ticket.status != "Booked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is only allowed for booked tickets.",
        )

    if ticket.payment_status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ticket is not awaiting payment.",
        )

    # Prevent multiple pending or successful payment records.
    existing_result = await db.execute(
        select(Payment).where(
            Payment.ticket_id == ticket.id,
            Payment.status.in_(["Pending", "Success", "Successful"]),
        )
    )
    existing_payment = existing_result.scalar_one_or_none()

    if existing_payment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending or successful payment already exists.",
        )

    payment = Payment(
        ticket_id=ticket.id,
        transaction_reference=f"MOCK-{secrets.token_hex(10).upper()}",
        amount=Decimal(str(ticket.total_amount)),
        payment_method=payment_data.payment_method,
        status="Pending",
    )

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return payment


@router.patch("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(
    payment_id: int,
    payment_data: PaymentProcess,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Lock the payment record while processing it.
    result = await db.execute(
        select(Payment)
        .join(Ticket, Payment.ticket_id == Ticket.id)
        .where(
            Payment.id == payment_id,
            Ticket.customer_id == current_user.id,
        )
        .with_for_update()
    )
    payment = result.scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    if payment.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This payment has already been processed.",
        )

    ticket_result = await db.execute(
        select(Ticket)
        .where(Ticket.id == payment.ticket_id)
        .with_for_update()
    )
    ticket = ticket_result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated ticket not found.",
        )

    if ticket.payment_status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The ticket is not awaiting payment.",
        )

    if payment_data.status == "Success":
        payment.status = "Success"
        payment.paid_at = datetime.now()
        ticket.payment_status = "Paid"
    else:
        payment.status = "Failed"
        ticket.payment_status = "Pending"

    await db.commit()
    await db.refresh(payment)

    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment)
        .join(Ticket, Payment.ticket_id == Ticket.id)
        .where(
            Payment.id == payment_id,
            Ticket.customer_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    return payment
