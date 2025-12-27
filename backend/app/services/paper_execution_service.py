import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..core.config import settings
from ..enums import OrderStatus as PaperOrderStatus
from ..enums import OrderType, ProductType, RiskAction, RiskEventType, Side
from ..models import PaperAccount, PaperFill, PaperOrder, PaperPosition
from ..risk_engine.calc import get_risk_snapshot
from ..risk_engine.engine import run_all_rules
from ..risk_engine.types import OrderIntent
from ..schemas.paper import PaperOrderRequest, PaperOrderResponse, PaperPositionResponse
from ..services.pricing_service import PricingService
from ..services.risk_service import RiskService


class PaperExecutionService:
    """Paper trading execution service with risk management integration."""

    def __init__(self, db: Session):
        self.db = db
        self.pricing_service = PricingService(db)
        self.risk_service = RiskService(db)

    def create_account(self, user_id: int, starting_cash: Optional[Decimal] = None) -> PaperAccount:
        if starting_cash is None:
            starting_cash = Decimal(settings.paper_starting_cash)

        account = PaperAccount(user_id=user_id, cash_balance=starting_cash, starting_cash=starting_cash)
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account(self, user_id: int) -> Optional[PaperAccount]:
        return self.db.query(PaperAccount).filter(PaperAccount.user_id == user_id).first()

    def place_order(self, user_id: int, order_request: PaperOrderRequest, skip_risk: bool = False) -> PaperOrderResponse:
        account = self.get_account(user_id)
        if not account:
            account = self.create_account(user_id)

        current_price = self.pricing_service.get_ltp_single(order_request.symbol)
        order_price = order_request.limit_price if order_request.order_type == OrderType.LIMIT else current_price
        if order_price is None:
            raise HTTPException(status_code=400, detail={"detail": "Price unavailable", "code": "PRICE_UNAVAILABLE"})

        if settings.enable_risk_enforcement and not skip_risk:
            order_intent = OrderIntent(
                symbol=order_request.symbol,
                side=order_request.side,
                qty=Decimal(order_request.qty),
                order_type=order_request.order_type,
                limit_price=order_request.limit_price,
                current_price=order_price,
                product=order_request.product,
                strategy_id=getattr(order_request, "strategy_id", None),
            )

            snapshot = get_risk_snapshot(self.db, user_id)
            limits = self.risk_service.get_effective_limits(user_id, order_intent.strategy_id)
            decision = run_all_rules(order_intent, snapshot, limits)

            if decision.action != RiskAction.ALLOW:
                event_type = self._map_action_to_event(decision.action)
                if decision.action == RiskAction.HALT_TRADING:
                    self.risk_service.set_halt(user_id, True, decision.message, strategy_id=order_intent.strategy_id)
                self.risk_service.log_event(
                    user_id=user_id,
                    event_type=event_type,
                    reason_code=decision.reason_code,
                    message=decision.message,
                    snapshot=snapshot,
                    strategy_id=order_intent.strategy_id,
                    symbol=order_intent.symbol,
                )
                status_code = 409 if decision.action == RiskAction.HALT_TRADING else 403
                raise HTTPException(status_code=status_code, detail={"detail": decision.message, "code": decision.reason_code})

        order = PaperOrder(
            id=str(uuid.uuid4()),
            account_id=account.id,
            strategy_id=order_request.strategy_id,
            symbol=order_request.symbol,
            side=order_request.side,
            qty=order_request.qty,
            order_type=order_request.order_type,
            limit_price=order_request.limit_price,
            product=order_request.product,
            tif=order_request.tif,
            status=PaperOrderStatus.OPEN,
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        # Publish order created event
        event = OrderCreatedEvent(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            order_type=order.order_type,
            limit_price=order.limit_price,
            product=order.product,
            status=order.status,
        )
        envelope = create_event_envelope(EventType.ORDER_CREATED, event, user_id)
        get_event_bus().publish(envelope)

        if order_request.order_type == OrderType.MARKET:
            self._execute_market_order(order, Decimal(order_price))

        return PaperOrderResponse.model_validate(order)

    def cancel_order(self, user_id: int, order_id: str) -> bool:
        order = (
            self.db.query(PaperOrder)
            .join(PaperAccount, PaperAccount.id == PaperOrder.account_id)
            .filter(PaperOrder.id == order_id, PaperAccount.user_id == user_id, PaperOrder.status == PaperOrderStatus.OPEN)
            .first()
        )

        if not order:
            return False

        order.status = PaperOrderStatus.CANCELLED
        order.reject_reason = "Cancelled by user"
        self.db.commit()
        return True

    def get_order(self, user_id: int, order_id: str) -> Optional[PaperOrder]:
        return (
            self.db.query(PaperOrder)
            .join(PaperAccount, PaperAccount.id == PaperOrder.account_id)
            .filter(PaperOrder.id == order_id, PaperAccount.user_id == user_id)
            .first()
        )

    def get_positions(self, user_id: int) -> List[PaperPositionResponse]:
        positions = (
            self.db.query(PaperPosition)
            .join(PaperAccount, PaperAccount.id == PaperPosition.account_id)
            .filter(PaperAccount.user_id == user_id, PaperPosition.net_qty != 0)
            .all()
        )

        responses: List[PaperPositionResponse] = []
        for pos in positions:
            ltp = self.pricing_service.get_ltp_single(pos.symbol) or pos.avg_price
            responses.append(
                PaperPositionResponse(
                    id=pos.id,
                    account_id=pos.account_id,
                    symbol=pos.symbol,
                    product=pos.product,
                    net_qty=pos.net_qty,
                    avg_price=pos.avg_price,
                    realized_pnl=pos.realized_pnl,
                    opened_at=pos.opened_at,
                    updated_at=pos.updated_at,
                )
            )
        return responses

    def list_fills(self, user_id: int) -> List[PaperFill]:
        return (
            self.db.query(PaperFill)
            .join(PaperOrder, PaperOrder.id == PaperFill.order_id)
            .join(PaperAccount, PaperAccount.id == PaperOrder.account_id)
            .filter(PaperAccount.user_id == user_id)
            .all()
        )

    def _execute_market_order(self, order: PaperOrder, price: Decimal):
        fill = PaperFill(order_id=order.id, symbol=order.symbol, qty=order.qty, price=price, fees=Decimal("0"), slippage=Decimal("0"))
        self.db.add(fill)

        order.status = PaperOrderStatus.FILLED

        self._update_position(order.account_id, order.symbol, order.side, order.qty, price)

        account = self.db.query(PaperAccount).filter(PaperAccount.id == order.account_id).first()
        notional = price * Decimal(order.qty)
        if order.side == Side.BUY:
            account.cash_balance -= notional
        else:
            account.cash_balance += notional

        self.db.commit()

    def _update_position(self, account_id: int, symbol: str, side: Side, qty: int, price: Decimal):
        position = (
            self.db.query(PaperPosition)
            .filter(PaperPosition.account_id == account_id, PaperPosition.symbol == symbol)
            .first()
        )

        if not position:
            position = PaperPosition(account_id=account_id, symbol=symbol, net_qty=0, avg_price=Decimal("0"))
            self.db.add(position)

        if side == Side.BUY:
            new_qty = position.net_qty + qty
            if new_qty != 0:
                new_avg_price = ((Decimal(position.net_qty) * position.avg_price) + (Decimal(qty) * price)) / Decimal(new_qty)
            else:
                new_avg_price = Decimal("0")
        else:
            new_qty = position.net_qty - qty
            new_avg_price = position.avg_price

        position.net_qty = new_qty
        position.avg_price = new_avg_price
        position.updated_at = datetime.utcnow()

        if position.net_qty == 0:
            self.db.delete(position)

    @staticmethod
    def _map_action_to_event(action: RiskAction) -> RiskEventType:
        if action == RiskAction.HALT_TRADING:
            return RiskEventType.HALT
        if action == RiskAction.FORCE_SQUARE_OFF:
            return RiskEventType.SQUAREOFF
        if action == RiskAction.REDUCE_QTY:
            return RiskEventType.ALLOW_REDUCED
        return RiskEventType.REJECT
