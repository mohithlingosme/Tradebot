from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from backend.app.enums import RiskEventType


class RiskLimitUpdate(BaseModel):
    daily_loss_inr: Optional[Decimal] = None
    daily_loss_pct: Optional[Decimal] = None
    max_position_value_inr: Optional[Decimal] = None
    max_position_qty: Optional[Decimal] = None
    max_gross_exposure_inr: Optional[Decimal] = None
    max_net_exposure_inr: Optional[Decimal] = None
    max_open_orders: Optional[int] = None
    cutoff_time: Optional[str] = None
    is_enabled: Optional[bool] = None


class RiskStatusResponse(BaseModel):
    is_enabled: bool
    is_halted: bool
    halted_reason: Optional[str]
    last_updated: Optional[datetime]


class RiskEventResponse(BaseModel):
    id: int
    ts: datetime
    user_id: int
    strategy_id: Optional[str]
    symbol: Optional[str]
    event_type: RiskEventType
    reason_code: str
    message: str
    snapshot: dict

    class Config:
        orm_mode = True


class HaltRequest(BaseModel):
    reason: str


class ResumeRequest(BaseModel):
    pass
