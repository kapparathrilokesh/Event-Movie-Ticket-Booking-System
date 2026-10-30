
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VenueCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    address: str = Field(min_length=3, max_length=255)
    city: str = Field(min_length=2, max_length=100)


class VenueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address: str | None = Field(default=None, min_length=3, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    is_active: bool | None = None


class VenueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    city: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
