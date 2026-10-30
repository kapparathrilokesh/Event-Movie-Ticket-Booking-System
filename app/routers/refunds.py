
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.refund import (
    RefundCreate,
    RefundProcess,
    RefundResponse,
)

router = APIRouter(prefix="/refunds", tags=["Refunds"])


@router.post(
    "/",
    response_model=RefundResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_refund(
    refund_data: RefundCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payment)
        .join(Ticket, Payment.ticket_id == Ticket.id)
        .where(
            Payment.id == refund_data.payment_id,
            Ticket.customer_id == current_user.id,
        )
        .with_for_update()
    )
    payment = result.scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found.",
        )

    if payment.status not in ("Success", "Successful"):
        raise HTTPException(
            status_code=400,
            detail="Only successful payments can be refunded.",
        )

    existing_result = await db.execute(
        select(Refund).where(
            Refund.payment_id == payment.id,
            Refund.status.in_(["Pending", "Approved"]),
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="A pending or approved refund already exists.",
        )

    refund = Refund(
        payment_id=payment.id,
        amount=Decimal(str(payment.amount)),
        reason=refund_data.reason,
        status="Pending",
    )

    db.add(refund)
    await db.commit()
    await db.refresh(refund)
    return refund


@router.patch("/{refund_id}/process", response_model=RefundResponse)
async def process_refund(
    refund_id: int,
    refund_data: RefundProcess,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can process refunds.",
        )

    result = await db.execute(
        select(Refund)
        .where(Refund.id == refund_id)
        .with_for_update()
    )
    refund = result.scalar_one_or_none()

    if refund is None:
        raise HTTPException(status_code=404, detail="Refund not found.")

    if refund.status != "Pending":
        raise HTTPException(
            status_code=409,
            detail="This refund has already been processed.",
        )

    if refund_data.status == "Approved":
        payment_result = await db.execute(
            select(Payment)
            .where(Payment.id == refund.payment_id)
            .with_for_update()
        )
        payment = payment_result.scalar_one_or_none()

        if payment is None or payment.status not in ("Success", "Successful"):
            raise HTTPException(
                status_code=400,
                detail="The associated payment is not refundable.",
            )

        # Mock refund only; no real money is transferred.
        payment.status = "Refunded"

    refund.status = refund_data.status
    refund.processed_at = datetime.now()

    await db.commit()
    await db.refresh(refund)
    return refund


@router.get("/{refund_id}", response_model=RefundResponse)
async def get_refund(
    refund_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Refund)
        .join(Payment, Refund.payment_id == Payment.id)
        .join(Ticket, Payment.ticket_id == Ticket.id)
        .where(Refund.id == refund_id)
    )

    if current_user.role != "Admin":
        query = query.where(Ticket.customer_id == current_user.id)

    result = await db.execute(query)
    refund = result.scalar_one_or_none()

    if refund is None:
        raise HTTPException(status_code=404, detail="Refund not found.")

    return refund
