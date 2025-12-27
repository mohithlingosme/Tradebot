from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..enums import Side, OrderType, OrderStatus


class PaperAccountResponse(BaseModel):
    id: int
    user_id: int
    currency: str
    starting_cash: Decimal
    cash_balance: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperOrderRequest(BaseModel):
    symbol: str
    side: Side
    qty: int = Field(gt=0)
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[Decimal] = None
    product: str = "MIS"  # MIS or CNC
    tif: str = "DAY"  # Time in force
    strategy_id: Optional[str] = None


class PaperOrderResponse(BaseModel):
    id: str
    account_id: int
    symbol: str
    side: Side
    qty: int
    order_type: OrderType
    limit_price: Optional[Decimal]
    product: str
    tif: str
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    reject_reason: Optional[str]

    class Config:
        from_attributes = True


class PaperFillResponse(BaseModel):
    id: int
    order_id: str
    symbol: str
    qty: int
    price: Decimal
    fees: Decimal
    slippage: Decimal
    filled_at: datetime

    class Config:
        from_attributes = True


class PaperPositionResponse(BaseModel):
    id: int
    account_id: int
    symbol: str
    product: str
    net_qty: int
    avg_price: Decimal
    realized_pnl: Decimal
    opened_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperLedgerResponse(BaseModel):
    id: int
    account_id: int
    type: str
    amount: Decimal
    meta: Optional[str]
    ts: datetime

    class Config:
        from_attributes = True


class PnLPaperResponse(BaseModel):
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
    day_pnl: Decimal


class ErrorResponse(BaseModel):
    detail: str
    code: str


# Request/Response models for API
class CreateAccountRequest(BaseModel):
    starting_cash: Optional[int] = None


class ListOrdersQuery(BaseModel):
    status: Optional[OrderStatus] = None
    symbol: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class ListFillsQuery(BaseModel):
    symbol: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class ModifyOrderRequest(BaseModel):
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
