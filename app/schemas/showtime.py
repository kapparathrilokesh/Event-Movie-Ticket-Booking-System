
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ShowtimeCreate(BaseModel):
    event_id: int = Field(gt=0)
    screen_id: int = Field(gt=0)
    starts_at: datetime
    ends_at: datetime
    base_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    language: str | None = Field(default=None, max_length=50)
    status: Literal["Scheduled", "Cancelled", "Completed"] = "Scheduled"

    @model_validator(mode="after")
    def validate_times(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at.")
        return self


class ShowtimeUpdate(BaseModel):
    screen_id: int | None = Field(default=None, gt=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    base_price: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    language: str | None = Field(default=None, max_length=50)
    status: Literal["Scheduled", "Cancelled", "Completed"] | None = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.starts_at is not None and self.ends_at is not None:
            if self.ends_at <= self.starts_at:
                raise ValueError("ends_at must be later than starts_at.")
        return self


class ShowtimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    screen_id: int | None
    starts_at: datetime
    ends_at: datetime
    base_price: Decimal
    language: str | None
    status: str
    created_at: datetime
    updated_at: datetime
