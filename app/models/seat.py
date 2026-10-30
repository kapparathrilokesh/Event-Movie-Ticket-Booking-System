
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Seat(Base):
    __tablename__ = "seats"

    __table_args__ = (
        UniqueConstraint(
            "screen_id",
            "row_label",
            "seat_number",
            name="uq_screen_row_seat",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    screen_id: Mapped[int] = mapped_column(
        ForeignKey("screens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_label: Mapped[str] = mapped_column(String(5), nullable=False)
    seat_number: Mapped[int] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(
        String(30), default="Standard", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
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

    screen: Mapped["Screen"] = relationship(back_populates="seats")
