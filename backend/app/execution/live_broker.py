from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .broker_interface import BrokerInterface
from ..config import settings
from ..enums import RiskAction, RiskEventType
from ..risk_engine.calc import get_risk_snapshot
from ..risk_engine.engine import run_all_rules
from ..risk_engine.types import OrderIntent
from ..schemas.paper import PaperOrderRequest, PaperOrderResponse, PaperPositionResponse
from ..services.risk_service import RiskService


class LiveBroker(BrokerInterface):
    def __init__(self, db: Session):
        self.db = db
        self.risk_service = RiskService(db)

    def place_order(self, user_id: int, order_request: PaperOrderRequest) -> PaperOrderResponse:
        """
        Places a live trading order after performing risk checks.
        This is a stub implementation.
        """
        if settings.enable_risk_enforcement:
            order_intent = OrderIntent(
                symbol=order_request.symbol,
                side=order_request.side,
                qty=order_request.qty,
                order_type=order_request.order_type,
                limit_price=order_request.limit_price,
                current_price=order_request.limit_price,
                product=order_request.product,
                strategy_id=getattr(order_request, "strategy_id", None),
            )

            snapshot = get_risk_snapshot(self.db, user_id)
            limits = self.risk_service.get_effective_limits(user_id, order_intent.strategy_id)

            decision = run_all_rules(order_intent, snapshot, limits)

            if decision.action != RiskAction.ALLOW:
                event_type = RiskEventType.HALT if decision.action == RiskAction.HALT_TRADING else RiskEventType.REJECT
                self.risk_service.log_event(
                    user_id=user_id,
                    event_type=event_type,
                    reason_code=decision.reason_code,
                    message=decision.message,
                    snapshot=snapshot,
                    strategy_id=order_intent.strategy_id,
                    symbol=order_intent.symbol,
                )
                raise HTTPException(status_code=403, detail={"detail": decision.message, "code": decision.reason_code})

        raise NotImplementedError("Live broker not implemented.")

    def get_positions(self, user_id: int) -> List[PaperPositionResponse]:
        """
        Retrieves live trading positions.
        This is a stub implementation.
        """
        raise NotImplementedError("Live broker not implemented.")
