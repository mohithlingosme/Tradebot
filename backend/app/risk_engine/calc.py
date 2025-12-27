from decimal import Decimal
from typing import Dict

from sqlalchemy.orm import Session

from backend.app.enums import OrderStatus
from backend.app.models import PaperAccount, PaperOrder, PaperPosition
from backend.app.risk_engine.types import RiskSnapshot
from backend.app.services.pricing_service import PricingService

ZERO = Decimal("0")


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return ZERO


def get_risk_snapshot(db: Session, user_id: int) -> RiskSnapshot:
    """
    Build a point-in-time risk snapshot for the given user.
    Uses Decimal math and batches price lookups to avoid N+1 queries.
    """
    paper_account = db.query(PaperAccount).filter(PaperAccount.user_id == user_id).first()
    if not paper_account:
        return RiskSnapshot(
            cash=ZERO,
            holdings_value=ZERO,
            positions_value=ZERO,
            gross_exposure=ZERO,
            net_exposure=ZERO,
            day_pnl=ZERO,
            day_pnl_pct=ZERO,
            open_orders_count=0,
            per_symbol_exposure={},
            per_symbol_qty={},
            last_price={},
        )

    pricing = PricingService(db)

    positions = db.query(PaperPosition).filter(PaperPosition.account_id == paper_account.id).all()
    symbols = [pos.symbol for pos in positions]
    ltps: Dict[str, Decimal] = pricing.get_ltp(symbols) if symbols else {}

    per_symbol_exposure: Dict[str, Decimal] = {}
    per_symbol_qty: Dict[str, Decimal] = {}
    last_price: Dict[str, Decimal] = {}

    gross_exposure = ZERO
    net_exposure = ZERO
    positions_value = ZERO
    cost_basis = ZERO
    realized_pnl = ZERO

    for pos in positions:
        ltp = _to_decimal(ltps.get(pos.symbol)) or _to_decimal(pos.avg_price)
        qty = _to_decimal(pos.net_qty)

        exposure = qty * ltp
        per_symbol_exposure[pos.symbol] = exposure
        per_symbol_qty[pos.symbol] = qty
        last_price[pos.symbol] = ltp

        gross_exposure += abs(exposure)
        net_exposure += exposure
        positions_value += exposure
        cost_basis += qty * _to_decimal(pos.avg_price)
        realized_pnl += _to_decimal(pos.realized_pnl)

    day_pnl_unrealized = positions_value - cost_basis
    day_pnl = realized_pnl + day_pnl_unrealized
    day_pnl_pct = ZERO
    if paper_account.starting_cash and paper_account.starting_cash != 0:
        day_pnl_pct = (day_pnl / _to_decimal(paper_account.starting_cash)) * Decimal("100")

    open_orders_count = db.query(PaperOrder).filter(
        PaperOrder.account_id == paper_account.id,
        PaperOrder.status.in_([OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIAL]),
    ).count()

    return RiskSnapshot(
        cash=_to_decimal(paper_account.cash_balance),
        holdings_value=ZERO,
        positions_value=positions_value,
        gross_exposure=gross_exposure,
        net_exposure=net_exposure,
        day_pnl=day_pnl,
        day_pnl_pct=day_pnl_pct,
        open_orders_count=open_orders_count,
        per_symbol_exposure=per_symbol_exposure,
        per_symbol_qty=per_symbol_qty,
        last_price=last_price,
    )
