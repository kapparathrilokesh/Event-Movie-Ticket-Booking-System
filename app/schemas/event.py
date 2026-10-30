
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = None
    event_type: str = Field(default="Movie", max_length=30)
    venue_id: int
    duration_minutes: int | None = Field(default=None, gt=0)
    language: str | None = Field(default=None, max_length=50)
    poster_url: str | None = Field(default=None, max_length=500)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    event_type: str | None = Field(default=None, max_length=30)
    venue_id: int | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    language: str | None = Field(default=None, max_length=50)
    poster_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    event_type: str
    venue_id: int
    duration_minutes: int | None
    language: str | None
    poster_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
