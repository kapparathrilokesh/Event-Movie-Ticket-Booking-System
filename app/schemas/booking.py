
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingCreate(BaseModel):
    showtime_id: int = Field(gt=0)
    seat_ids: list[int] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def validate_seat_ids(self):
        if any(seat_id <= 0 for seat_id in self.seat_ids):
            raise ValueError("Every seat ID must be positive.")

        if len(set(self.seat_ids)) != len(self.seat_ids):
            raise ValueError("Duplicate seat IDs are not allowed.")

        return self


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_reference: str
    customer_id: int
    showtime_id: int
    quantity: int
    total_amount: Decimal
    status: str
    payment_status: str
    booked_at: datetime
    qr_code_path: str | None = None