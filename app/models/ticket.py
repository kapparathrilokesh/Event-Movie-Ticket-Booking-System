
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    booking_reference: Mapped[str] = mapped_column(
        String(30), unique=True, index=True, nullable=False
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    showtime_id: Mapped[int] = mapped_column(
        ForeignKey("showtimes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), default="Booked", nullable=False
    )

    payment_status: Mapped[str] = mapped_column(
        String(20), default="Pending", nullable=False
    )

    qr_code_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    customer: Mapped["User"] = relationship()
    showtime: Mapped["Showtime"] = relationship()
