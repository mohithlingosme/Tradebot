import pytest
from decimal import Decimal
from fastapi import HTTPException

from backend.app.enums import OrderType, Side
from backend.app.schemas.paper import PaperOrderRequest
from backend.app.services.paper_execution_service import PaperExecutionService
from backend.app.services.risk_service import RiskService


@pytest.fixture
def paper_service(db_session):
    return PaperExecutionService(db_session)


@pytest.fixture
def risk_service(db_session):
    return RiskService(db_session)


def test_order_rejected_when_halted(paper_service: PaperExecutionService, risk_service: RiskService):
    user_id = 1
    risk_service.set_halt(user_id, True, "manual halt")

    with pytest.raises(HTTPException) as exc:
        paper_service.place_order(
            user_id,
            PaperOrderRequest(
                symbol="AAPL",
                side=Side.BUY,
                qty=1,
                order_type=OrderType.MARKET,
                product="MIS",
            ),
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "TRADING_HALTED"


def test_order_blocked_by_position_limit(paper_service: PaperExecutionService, risk_service: RiskService):
    user_id = 2
    risk_service.upsert_limits(user_id, {"max_position_qty": 1})

    with pytest.raises(HTTPException) as exc:
        paper_service.place_order(
            user_id,
            PaperOrderRequest(
                symbol="AAPL",
                side=Side.BUY,
                qty=5,
                order_type=OrderType.MARKET,
                product="MIS",
            ),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "MAX_POSITION_QTY_BREACHED"
