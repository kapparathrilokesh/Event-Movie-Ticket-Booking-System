
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SeatBooking(Base):
    __tablename__ = "seat_bookings"

    __table_args__ = (
        UniqueConstraint(
            "showtime_id",
            "seat_id",
            name="uq_showtime_seat_booking",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    showtime_id: Mapped[int] = mapped_column(
        ForeignKey("showtimes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    seat_id: Mapped[int] = mapped_column(
        ForeignKey("seats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20), default="Booked", nullable=False
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ticket: Mapped["Ticket"] = relationship()
    showtime: Mapped["Showtime"] = relationship()
    seat: Mapped["Seat"] = relationship()
