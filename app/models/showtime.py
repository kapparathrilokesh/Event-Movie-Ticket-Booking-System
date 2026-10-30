
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Showtime(Base):
    __tablename__ = "showtimes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    screen_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("screens.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    base_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    language: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), default="Scheduled", nullable=False
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

    event: Mapped["Event"] = relationship()
    screen: Mapped[Optional["Screen"]] = relationship()
