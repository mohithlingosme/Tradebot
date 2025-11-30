"""
Paper Trading API endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

from .auth import get_current_active_user
from trading_engine.paper_trading import get_paper_trading_engine, PaperTradingEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/paper-trading", tags=["paper-trading"])


class PlaceOrderRequest(BaseModel):
    """Place order request model."""
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    order_type: str = "market"  # 'market', 'limit', 'stop'
    price: Optional[float] = None
    stop_price: Optional[float] = None
    current_market_price: Optional[float] = None


class OrderResponse(BaseModel):
    """Order response model."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    price: Optional[float]
    status: str
    filled_quantity: float
    avg_fill_price: float
    fill_price: Optional[float]
    created_at: str
    filled_at: Optional[str]


@router.post("/place-order", response_model=OrderResponse)
async def place_order(
    request: PlaceOrderRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Place a paper trading order.

    Args:
        request: Order details
        current_user: Authenticated user

    Returns:
        Order execution result
    """
    try:
        username = current_user["username"]
        engine = get_paper_trading_engine(username)

        # Validate order
        if request.side.lower() not in ['buy', 'sell']:
            raise HTTPException(status_code=400, detail="Side must be 'buy' or 'sell'")

        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")

        if request.order_type == "limit" and not request.price:
            raise HTTPException(status_code=400, detail="Limit orders require a price")

        if request.order_type == "stop" and not request.stop_price:
            raise HTTPException(status_code=400, detail="Stop orders require a stop_price")

        # Place order
        result = engine.place_order(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_type=request.order_type,
            price=request.price,
            stop_price=request.stop_price,
            current_market_price=request.current_market_price,
        )

        if result.get("status") == "rejected":
            raise HTTPException(status_code=400, detail=result.get("message", "Order rejected"))

        return OrderResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing paper trading order: {e}")
        raise HTTPException(status_code=500, detail="Order placement failed")


@router.get("/portfolio")
async def get_paper_portfolio(
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get paper trading portfolio summary.

    Returns:
        Portfolio summary
    """
    try:
        username = current_user["username"]
        engine = get_paper_trading_engine(username)
        portfolio = engine.get_portfolio_summary()
        return portfolio
    except Exception as e:
        logger.error(f"Error getting paper portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to get portfolio")


@router.get("/positions")
async def get_paper_positions(
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get paper trading positions.

    Returns:
        List of positions
    """
    try:
        username = current_user["username"]
        engine = get_paper_trading_engine(username)
        positions = engine.get_positions()
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        logger.error(f"Error getting paper positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get positions")


@router.get("/orders")
async def get_paper_orders(
    limit: int = 50,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get paper trading order history.

    Args:
        limit: Maximum number of orders to return

    Returns:
        List of orders
    """
    try:
        username = current_user["username"]
        engine = get_paper_trading_engine(username)
        orders = engine.get_orders(limit=limit)
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error getting paper orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to get orders")


@router.get("/trades")
async def get_paper_trades(
    limit: int = 50,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get paper trading trade history.

    Args:
        limit: Maximum number of trades to return

    Returns:
        List of executed trades
    """
    try:
        username = current_user["username"]
        engine = get_paper_trading_engine(username)
        trades = engine.get_trade_history(limit=limit)
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        logger.error(f"Error getting paper trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trades")


class ResetPortfolioRequest(BaseModel):
    """Reset portfolio request model."""
    initial_cash: Optional[float] = 100000.0


@router.post("/reset")
async def reset_paper_portfolio(
    request: ResetPortfolioRequest = ResetPortfolioRequest(),
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Reset paper trading portfolio.

    Args:
        request: Reset options (initial cash amount)

    Returns:
        Reset confirmation
    """
    try:
        username = current_user["username"]
        engine = get_paper_trading_engine(username)
        engine.reset_portfolio(initial_cash=request.initial_cash)
        return {
            "message": "Portfolio reset successfully",
            "initial_cash": request.initial_cash
        }
    except Exception as e:
        logger.error(f"Error resetting paper portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset portfolio")


@router.post("/update-prices")
async def update_paper_prices(
    price_updates: Dict[str, float],
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Update current market prices for positions.

    Args:
        price_updates: Dictionary of symbol -> current_price

    Returns:
        Update confirmation
    """
    try:
        username = current_user["username"]
        engine = get_paper_trading_engine(username)
        engine.update_prices(price_updates)
        return {"message": "Prices updated successfully"}
    except Exception as e:
        logger.error(f"Error updating prices: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prices")

