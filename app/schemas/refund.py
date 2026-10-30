
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RefundCreate(BaseModel):
    payment_id: int = Field(gt=0)
    reason: str | None = Field(default=None, max_length=2000)


class RefundProcess(BaseModel):
    status: str = Field(pattern=r"^(Approved|Rejected)$")


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_id: int
    amount: Decimal
    reason: str | None
    status: str
    processed_at: datetime | None
    created_at: datetime
