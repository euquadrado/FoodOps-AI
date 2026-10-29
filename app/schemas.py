from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    restaurant_name: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payment_method: str
    amount: Decimal
    status: str
    created_at: datetime


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: str
    description: str
    created_at: datetime


class DiagnoseRequest(BaseModel):
    message: str = Field(min_length=3, max_length=2000, pattern=r"\S")


class Diagnosis(BaseModel):
    order_id: int
    status: str
    summary: str
    problem: str
    diagnosis: str
    evidence: list[str]
    hypotheses: list[str] = Field(default_factory=list)
    recommendation: str
    mode: Literal["demo", "ai"] = "demo"
    tools_used: list[str] = Field(default_factory=list)
    elapsed_ms: float = 0
    ai_explanation: str | None = None
