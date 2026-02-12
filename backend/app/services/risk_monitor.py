import asyncio

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database import SessionLocal
from backend.app.enums import OrderStatus, OrderType, RiskAction, RiskEventType, Side
from backend.app.models import PaperAccount, PaperOrder, PaperPosition, User
from backend.app.risk_engine import calc, rules
from backend.app.services.paper_execution_service import PaperExecutionService
from backend.app.services.risk_service import RiskService
from backend.app.schemas.paper import PaperOrderRequest


async def monitor_risk(poll_interval_seconds: int = 30):
    """Periodically recompute risk snapshots and trigger halts/square-offs."""
    while True:
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.is_active == True).all()
            risk_svc = RiskService(db)
            for user in users:
                limits = risk_svc.get_effective_limits(user.id)
                if not limits.is_enabled or limits.is_halted:
                    continue

                snapshot = calc.get_risk_snapshot(db, user.id)
                halt_decision = rules.rule_max_daily_loss_inr(snapshot, limits) or rules.rule_max_daily_loss_pct(snapshot, limits)

                if halt_decision and halt_decision.action == RiskAction.HALT_TRADING:
                    risk_svc.set_halt(user.id, True, halt_decision.message)
                    risk_svc.log_event(
                        user_id=user.id,
                        event_type=RiskEventType.HALT,
                        reason_code=halt_decision.reason_code,
                        message=halt_decision.message,
                        snapshot=snapshot,
                    )
                    if settings.enable_force_square_off:
                        _force_square_off(db, user.id)
        finally:
            db.close()

        await asyncio.sleep(poll_interval_seconds)


def _force_square_off(db: Session, user_id: int):
    account = db.query(PaperAccount).filter(PaperAccount.user_id == user_id).first()
    if not account:
        return

    positions = (
        db.query(PaperPosition)
        .filter(PaperPosition.account_id == account.id, PaperPosition.net_qty != 0)
        .all()
    )
    if not positions:
        return

    execution_service = PaperExecutionService(db)
    for position in positions:
        exit_side = Side.SELL if position.net_qty > 0 else Side.BUY
        open_exit = (
            db.query(PaperOrder)
            .filter(
                PaperOrder.account_id == account.id,
                PaperOrder.symbol == position.symbol,
                PaperOrder.side == exit_side,
                PaperOrder.status.in_([OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIAL]),
            )
            .first()
        )
        if open_exit:
            continue

        execution_service.place_order(
            user_id,
            PaperOrderRequest(
                symbol=position.symbol,
                side=exit_side,
                qty=abs(position.net_qty),
                order_type=OrderType.MARKET,
                product=position.product,
            ),
            skip_risk=True,
        )
