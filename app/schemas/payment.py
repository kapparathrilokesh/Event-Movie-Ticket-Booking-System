
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    ticket_id: int = Field(gt=0)
    payment_method: Literal["Mock"] = "Mock"


class PaymentProcess(BaseModel):
    status: Literal["Success", "Failed"]


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    transaction_reference: str | None
    amount: Decimal
    payment_method: str
    status: str
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime
