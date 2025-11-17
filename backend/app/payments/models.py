from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Plan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price_inr: int
    interval: str = "monthly"
    features: dict = Field(default_factory=dict, sa_column_kwargs={"nullable": False})


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    plan_id: int = Field(foreign_key="plan.id")
    razorpay_subscription_id: str | None = Field(default=None, unique=True)
    status: str = Field(default="pending", index=True)
    current_period_end: datetime | None = None


class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id")
    amount_inr: int
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    razorpay_invoice_id: str | None = None
