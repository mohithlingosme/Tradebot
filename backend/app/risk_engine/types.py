from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.app.enums import OrderType, RiskAction, Side


class OrderIntent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    symbol: str
    side: Side
    qty: Decimal
    order_type: OrderType
    limit_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    product: str
    strategy_id: Optional[str] = None


class RiskSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    cash: Decimal
    holdings_value: Decimal
    positions_value: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    day_pnl: Decimal
    day_pnl_pct: Decimal
    open_orders_count: int
    per_symbol_exposure: Dict[str, Decimal] = Field(default_factory=dict)
    per_symbol_qty: Dict[str, Decimal] = Field(default_factory=dict)
    last_price: Dict[str, Decimal] = Field(default_factory=dict)


class RiskDecision(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    action: RiskAction
    allowed_qty: Optional[Decimal] = None
    reason_code: str
    message: str
    breached_limits: List[str] = Field(default_factory=list)
