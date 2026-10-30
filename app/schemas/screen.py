
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScreenCreate(BaseModel):
    venue_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)


class ScreenUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class ScreenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venue_id: int
    name: str
    total_seats: int
    created_at: datetime
    updated_at: datetime
