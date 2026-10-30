
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SeatCreate(BaseModel):
    screen_id: int = Field(gt=0)
    row_label: str = Field(min_length=1, max_length=5)
    seat_number: int = Field(gt=0)
    category: str = Field(default="Standard", min_length=1, max_length=30)


class SeatUpdate(BaseModel):
    row_label: str | None = Field(default=None, min_length=1, max_length=5)
    seat_number: int | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1, max_length=30)
    is_active: bool | None = None


class SeatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    screen_id: int
    row_label: str
    seat_number: int
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
