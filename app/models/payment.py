
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )

    amount: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    payment_method: Mapped[str] = mapped_column(
        String(30), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), default="Pending", nullable=False
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    ticket: Mapped["Ticket"] = relationship()
