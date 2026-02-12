import pytest
from decimal import Decimal
from sqlalchemy.orm import Session
from backend.app.services.paper_execution_service import PaperExecutionService
from backend.app.schemas.paper import PaperOrderRequest
from backend.app.enums import Side, OrderType


@pytest.fixture
def paper_service(db_session: Session):
    return PaperExecutionService(db_session)


def test_create_account(paper_service: PaperExecutionService, db_session: Session):
    """Test creating a paper account."""
    user_id = 1
    account = paper_service.create_account(user_id, starting_cash=Decimal('100000'))

    assert account.user_id == user_id
    assert account.cash_balance == Decimal('100000')
    assert account.starting_cash == Decimal('100000')


def test_place_market_buy_order(paper_service: PaperExecutionService, db_session: Session):
    """Test placing a market buy order."""
    user_id = 1
    paper_service.create_account(user_id)

    order_request = PaperOrderRequest(
        symbol="AAPL",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.MARKET,
        product="MIS"
    )

    order = paper_service.place_order(user_id, order_request)

    assert order.symbol == "AAPL"
    assert order.side == Side.BUY
    assert order.qty == 10
    assert order.status.name == "FILLED"  # Should fill immediately

    # Check fill was created
    fills = paper_service.list_fills(user_id)
    assert len(fills) == 1
    assert fills[0].qty == 10

    # Check position was created
    positions = paper_service.get_positions(user_id)
    assert len(positions) == 1
    assert positions[0].net_qty == 10
    assert positions[0].symbol == "AAPL"


def test_place_market_sell_order(paper_service: PaperExecutionService, db_session: Session):
    """Test placing a market sell order after buying."""
    user_id = 1
    paper_service.create_account(user_id)

    # Buy first
    buy_request = PaperOrderRequest(
        symbol="AAPL",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.MARKET,
        product="MIS"
    )
    paper_service.place_order(user_id, buy_request)

    # Sell
    sell_request = PaperOrderRequest(
        symbol="AAPL",
        side=Side.SELL,
        qty=10,
        order_type=OrderType.MARKET,
        product="MIS"
    )
    order = paper_service.place_order(user_id, sell_request)

    assert order.status.name == "FILLED"

    # Check position was closed
    positions = paper_service.get_positions(user_id)
    assert len(positions) == 0  # Position closed


def test_insufficient_cash_cnc(paper_service: PaperExecutionService, db_session: Session):
    """Test CNC order rejection due to insufficient cash."""
    user_id = 1
    paper_service.create_account(user_id, starting_cash=Decimal('100'))  # Low cash

    order_request = PaperOrderRequest(
        symbol="AAPL",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.MARKET,
        product="CNC"  # Requires cash
    )

    with pytest.raises(ValueError) as exc_info:
        paper_service.place_order(user_id, order_request)

    assert "INSUFFICIENT_CASH" in str(exc_info.value)


def test_limit_order_no_fill(paper_service: PaperExecutionService, db_session: Session):
    """Test limit order that doesn't fill immediately."""
    user_id = 1
    paper_service.create_account(user_id)

    order_request = PaperOrderRequest(
        symbol="AAPL",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.LIMIT,
        limit_price=Decimal('50.00'),  # Low price, won't match LTP
        product="MIS"
    )

    order = paper_service.place_order(user_id, order_request)

    assert order.status.name == "OPEN"  # Should remain open

    # No fills
    fills = paper_service.list_fills(user_id)
    assert len(fills) == 0

    # No positions
    positions = paper_service.get_positions(user_id)
    assert len(positions) == 0


def test_cancel_order(paper_service: PaperExecutionService, db_session: Session):
    """Test cancelling an open order."""
    user_id = 1
    paper_service.create_account(user_id)

    # Place limit order that won't fill
    order_request = PaperOrderRequest(
        symbol="AAPL",
        side=Side.BUY,
        qty=10,
        order_type=OrderType.LIMIT,
        limit_price=Decimal('50.00'),
        product="MIS"
    )
    order = paper_service.place_order(user_id, order_request)

    # Cancel order
    success = paper_service.cancel_order(user_id, order.id)
    assert success

    # Check order status
    updated_order = paper_service.get_order(user_id, order.id)
    assert updated_order.status.name == "CANCELLED"
