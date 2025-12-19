import math
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette import status
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.api import auth as auth_service
from backend.app.schemas import (
    OrderBookAnalyticsResponse,
    OrderBookHistoryPoint,
    OrderBookLevel,
    RegimeHistoryPoint,
    RegimeResponse,
)
from backend.services.market_data import fetch_order_book_history, fetch_recent_candles
from analytics import OrderBookImbalanceAnalyzer, RegimeDetector
from models import User

# Database setup (simplified)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./finbot.db")
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

class LoginRequest(BaseModel):
    username: str
    password: str

class PortfolioResponse(BaseModel):
    cash: float
    equity: float
    buying_power: float

class TradeRequest(BaseModel):
    symbol: str
    qty: float
    side: str

class TradeResponse(BaseModel):
    symbol: str
    side: str
    filled_qty: float
    avg_fill_price: float
    status: str = "filled"

class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: str

class IndicatorPayload(BaseModel):
    timestamp: List[str]
    price: List[float]
    indicators: Dict[str, List[Optional[float]]]

class PositionSnapshot(BaseModel):
    symbol: str
    direction: str
    qty: float
    entry_price: float
    mark_price: float
    status: str
    last_updated: str

class PositionRecord(TypedDict):
    qty: float
    avg_entry_price: float
    last_fill_price: float
    last_update: str

app = FastAPI()

# CORS middleware
frontend_origins = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:5175"
)
allow_origin_list = [
    origin.strip() for origin in frontend_origins.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

portfolio_state: Dict[str, float] = {
    "cash": 125_000.0,
    "equity": 175_000.0,
    "buying_power": 200_000.0,
}
positions: Dict[str, PositionRecord] = {}
latest_price_cache: Dict[str, float] = {}
regime_detector = RegimeDetector(window=60, min_history=120)
order_book_analyzer = OrderBookImbalanceAnalyzer(depth=5, threshold=0.15)


def _base_price(symbol: str) -> float:
    symbol_upper = symbol.upper()
    if "BTC" in symbol_upper:
        return 45_000.0
    if "ETH" in symbol_upper:
        return 3_200.0
    if "EUR/USD" in symbol_upper or "USD" in symbol_upper:
        return 1.12
    if "AAPL" in symbol_upper:
        return 190.0
    return 100.0


def _moving_average(values: List[float], window: int) -> List[Optional[float]]:
    averaged: List[Optional[float]] = []
    for idx in range(len(values)):
        start = max(0, idx - window + 1)
        window_slice = values[start : idx + 1]
        averaged.append(round(sum(window_slice) / len(window_slice), 2))
    return averaged


def _exponential_moving_average(values: List[float], window: int) -> List[Optional[float]]:
    ema_values: List[Optional[float]] = []
    multiplier = 2 / (window + 1)
    ema: Optional[float] = None
    for value in values:
        if ema is None:
            ema = value
        else:
            ema = (value - ema) * multiplier + ema
        ema_values.append(round(ema, 2))
    return ema_values


def _rsi(values: List[float], window: int = 14) -> List[Optional[float]]:
    rsis: List[Optional[float]] = [None]
    avg_gain: Optional[float] = None
    avg_loss: Optional[float] = None
    for idx in range(1, len(values)):
        change = values[idx] - values[idx - 1]
        gain = max(change, 0.0)
        loss = max(-change, 0.0)
        if idx < window:
            avg_gain = gain if avg_gain is None else avg_gain + gain
            avg_loss = loss if avg_loss is None else avg_loss + loss
            rsis.append(None)
            if idx == window - 1 and avg_gain is not None and avg_loss is not None:
                avg_gain /= window
                avg_loss /= window
            continue
        if avg_gain is None or avg_loss is None:
            avg_gain = gain / window
            avg_loss = loss / window
        else:
            avg_gain = ((avg_gain * (window - 1)) + gain) / window
            avg_loss = ((avg_loss * (window - 1)) + loss) / window
        if avg_loss == 0:
            rs_value = 100.0
        else:
            rs = avg_gain / avg_loss if avg_loss else 0
            rs_value = 100 - (100 / (1 + rs)) if rs != 0 else 0
        rsis.append(round(rs_value, 2))
    return rsis


def _generate_indicator_payload(symbol: str, points: int = 120) -> IndicatorPayload:
    now = datetime.utcnow()
    timestamps = [
        (now - timedelta(minutes=(points - idx))).isoformat()
        for idx in range(points)
    ]
    base_price = _base_price(symbol)
    prices: List[float] = []
    current_price = base_price
    for idx in range(points):
        seasonal = math.sin(idx / 6) * base_price * 0.002
        shock = random.uniform(-1, 1) * base_price * 0.0015
        current_price = max(0.5, current_price + seasonal + shock)
        prices.append(round(current_price, 2))
    latest_price_cache[symbol.upper()] = prices[-1]
    sma_fast = _moving_average(prices, 5)
    sma_slow = _moving_average(prices, 10)
    ema_12 = _exponential_moving_average(prices, 12)
    ema_26 = _exponential_moving_average(prices, 26)
    macd_line = [
        round((ema_12[idx] or prices[idx]) - (ema_26[idx] or prices[idx]), 2)
        for idx in range(points)
    ]
    signal_line = _exponential_moving_average(
        [val if val is not None else 0 for val in macd_line], 9
    )
    rsi_14 = _rsi(prices, 14)
    indicators = {
        "sma_fast": sma_fast,
        "sma_slow": sma_slow,
        "ema_12": ema_12,
        "ema_26": ema_26,
        "macd": macd_line,
        "macd_signal": signal_line,
        "rsi_14": rsi_14,
    }
    return IndicatorPayload(timestamp=timestamps, price=prices, indicators=indicators)


def _ensure_price(symbol: str) -> float:
    symbol_key = symbol.upper()
    if symbol_key not in latest_price_cache:
        snapshot = _generate_indicator_payload(symbol_key)
        latest_price_cache[symbol_key] = snapshot.price[-1]
    return latest_price_cache[symbol_key]

def _get_position_entry(symbol: str) -> PositionRecord:
    symbol_key = symbol.upper()
    if symbol_key not in positions:
        positions[symbol_key] = {
            "qty": 0.0,
            "avg_entry_price": 0.0,
            "last_fill_price": 0.0,
            "last_update": datetime.utcnow().isoformat(),
        }
    return positions[symbol_key]


def _update_position(symbol: str, qty_delta: float, fill_price: float) -> None:
    entry = _get_position_entry(symbol)
    current_qty = entry["qty"]
    new_qty = current_qty + qty_delta
    if abs(new_qty) < 1e-9:
        new_qty = 0.0
    same_direction_add = current_qty == 0 or (
        (current_qty > 0 and new_qty > 0 and qty_delta > 0)
        or (current_qty < 0 and new_qty < 0 and qty_delta < 0)
    )
    flipped_direction = (current_qty > 0 and new_qty < 0) or (current_qty < 0 and new_qty > 0)
    if same_direction_add and new_qty != 0:
        numerator = (abs(current_qty) * entry["avg_entry_price"]) + (abs(qty_delta) * fill_price)
        entry_price = numerator / abs(new_qty)
    elif flipped_direction:
        entry_price = fill_price
    else:
        entry_price = entry["avg_entry_price"]

    entry["qty"] = round(new_qty, 8)
    entry["avg_entry_price"] = round(entry_price, 2)
    entry["last_fill_price"] = round(fill_price, 2)
    entry["last_update"] = datetime.utcnow().isoformat()


def _build_position_snapshots() -> List[PositionSnapshot]:
    snapshots: List[PositionSnapshot] = []
    for symbol, state in positions.items():
        qty = state["qty"]
        direction = "long" if qty > 0 else "short" if qty < 0 else "flat"
        status = "open" if qty != 0 else "closed"
        entry_price = state["avg_entry_price"] or state["last_fill_price"] or _ensure_price(symbol)
        mark_price = _ensure_price(symbol)
        snapshots.append(
            PositionSnapshot(
                symbol=symbol,
                direction=direction,
                qty=round(qty, 4),
                entry_price=round(entry_price, 2),
                mark_price=round(mark_price, 2),
                status=status,
                last_updated=state["last_update"],
            )
        )
    return snapshots


def _recalculate_portfolio(symbol: str, qty: float, side: str) -> float:
    price = _ensure_price(symbol)
    total_value = qty * price
    symbol_key = symbol.upper()
    side_lower = side.lower()
    qty_delta = qty if side_lower == "buy" else -qty
    _update_position(symbol_key, qty_delta, price)
    if side_lower == "buy":
        portfolio_state["cash"] = max(0.0, portfolio_state["cash"] - total_value)
    else:
        portfolio_state["cash"] += total_value
    notional = 0.0
    for sym, position_state in positions.items():
        position_qty = position_state["qty"]
        if position_qty <= 0:
            continue
        notional += position_qty * _ensure_price(sym)
    portfolio_state["equity"] = round(portfolio_state["cash"] + notional, 2)
    portfolio_state["buying_power"] = round(portfolio_state["cash"] * 2, 2)
    return price


async def get_current_user(
    token: str = Depends(auth_service.oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError as exc:  # pragma: no cover - defensive
        raise credentials_exception from exc

    user = await auth_service.get_user(db, username)
    if user is None:
        raise credentials_exception
    return user


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/auth/login", response_model=auth_service.TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(
        db, login_data.username, login_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(current_user: User = Depends(get_current_user)):
    return portfolio_state


@app.get("/positions", response_model=List[PositionSnapshot])
async def get_positions(current_user: User = Depends(get_current_user)):
    return _build_position_snapshots()


@app.get("/analytics/regime/{symbol:path}", response_model=RegimeResponse)
async def get_regime_analysis(
    symbol: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    candles = await fetch_recent_candles(session, symbol, limit=720)
    if not candles:
        raise HTTPException(status_code=404, detail="No market data for symbol")
    try:
        analysis = regime_detector.evaluate(candles)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RegimeResponse(
        symbol=analysis.symbol,
        current_regime=analysis.current_regime,
        probability=analysis.probability,
        realized_volatility=analysis.realized_volatility,
        atr=analysis.atr,
        window=analysis.window,
        updated_at=analysis.updated_at,
        history=[
            RegimeHistoryPoint(
                timestamp=point.timestamp,
                label=point.label,
                probability=point.probability,
                volatility=point.volatility,
            )
            for point in analysis.history
        ],
    )


@app.get("/analytics/order-book/{symbol:path}", response_model=OrderBookAnalyticsResponse)
async def get_order_book_analytics(
    symbol: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    snapshots = await fetch_order_book_history(session, symbol, limit=60)
    if not snapshots:
        raise HTTPException(status_code=404, detail="No order book depth available")
    try:
        analysis = order_book_analyzer.analyze(snapshots)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    latest = analysis.snapshot
    return OrderBookAnalyticsResponse(
        symbol=latest.symbol,
        timestamp=latest.timestamp,
        imbalance=analysis.imbalance,
        state=analysis.state,
        spread=analysis.spread,
        buy_pressure=analysis.buy_pressure,
        sell_pressure=analysis.sell_pressure,
        best_bid=latest.best_bid,
        best_ask=latest.best_ask,
        bids=[
            OrderBookLevel(price=level.price, size=level.size)
            for level in latest.bids[: order_book_analyzer.depth]
        ],
        asks=[
            OrderBookLevel(price=level.price, size=level.size)
            for level in latest.asks[: order_book_analyzer.depth]
        ],
        history=[
            OrderBookHistoryPoint(
                timestamp=point.timestamp,
                imbalance=point.imbalance,
                state=point.state,
            )
            for point in analysis.history
        ],
    )


@app.post("/trades", response_model=TradeResponse)
async def place_trade(payload: TradeRequest, current_user: User = Depends(get_current_user)):
    if payload.side.lower() not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="Invalid trade side")
    if payload.qty <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    fill_price = _recalculate_portfolio(payload.symbol, payload.qty, payload.side)
    return TradeResponse(
        symbol=payload.symbol.upper(),
        side=payload.side.lower(),
        filled_qty=payload.qty,
        avg_fill_price=round(fill_price, 2),
        status="filled",
    )


@app.get("/price/{symbol:path}", response_model=PriceResponse)
async def get_price(symbol: str, current_user: User = Depends(get_current_user)):
    snapshot = _generate_indicator_payload(symbol.upper(), points=30)
    price = snapshot.price[-1]
    timestamp = snapshot.timestamp[-1]
    return PriceResponse(symbol=symbol.upper(), price=price, timestamp=timestamp)


@app.get("/indicators/{symbol:path}", response_model=IndicatorPayload)
async def indicators(symbol: str, current_user: User = Depends(get_current_user)):
    return _generate_indicator_payload(symbol.upper())
