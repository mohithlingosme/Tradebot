# Paper Execution Module

This document describes the paper trading execution module for the FinBot trading platform.

## Overview

The paper execution module provides a realistic simulation of order execution, position management, and PnL tracking without real financial risk. It implements the same interface as live brokers, allowing strategies to switch between paper and live execution seamlessly.

## Features

- **Order Types**: MARKET, LIMIT
- **Product Types**: MIS (Margin Intraday Square-off), CNC (Cash and Carry)
- **Order States**: PENDING → OPEN → PARTIALLY_FILLED → FILLED → CANCELLED/REJECTED
- **Slippage & Fees**: Configurable slippage and brokerage fees
- **Risk Checks**: Cash balance validation for CNC orders
- **Position Management**: Real-time position tracking with average price calculation
- **PnL Tracking**: Realized and unrealized PnL calculation

## Configuration

Add these environment variables to your `.env` file:

```env
EXECUTION_MODE=paper
PAPER_STARTING_CASH=100000
SLIPPAGE_BPS=5
BROKERAGE_FLAT=0
BROKERAGE_BPS=0
PAPER_ENFORCE_MARKET_HOURS=false
```

## API Endpoints

### Account Management

#### Create Paper Account
```bash
POST /paper/account/create
Content-Type: application/json

{
  "starting_cash": 100000
}
```

#### Get Account
```bash
GET /paper/account
```

### Order Management

#### Place Order
```bash
POST /paper/orders
Content-Type: application/json

{
  "symbol": "AAPL",
  "side": "BUY",
  "qty": 10,
  "order_type": "MARKET",
  "product": "MIS"
}
```

#### List Orders
```bash
GET /paper/orders?status=OPEN&symbol=AAPL&limit=50&offset=0
```

#### Get Order
```bash
GET /paper/orders/{order_id}
```

#### Cancel Order
```bash
POST /paper/orders/{order_id}/cancel
```

#### Modify Order
```bash
PATCH /paper/orders/{order_id}
Content-Type: application/json

{
  "limit_price": 150.50
}
```

### Trading Data

#### List Fills
```bash
GET /paper/fills?symbol=AAPL&limit=50&offset=0
```

#### Get Positions
```bash
GET /paper/positions
```

#### Get PnL Summary
```bash
GET /paper/pnl/summary
```

## Execution Logic

### Price Determination

- **MARKET Orders**: Execute at LTP ± slippage
  - BUY: `executed_price = LTP + slippage`
  - SELL: `executed_price = LTP - slippage`
- **LIMIT Orders**: Fill only if conditions met
  - BUY: Fill if `LTP <= limit_price`
  - SELL: Fill if `LTP >= limit_price`

### Slippage Model

```
slippage = price * (SLIPPAGE_BPS / 10000)
```

### Fees Model

```
brokerage = BROKERAGE_FLAT + (notional_value * BROKERAGE_BPS / 10000)
total_fees = brokerage
```

### Risk Checks

- **MIS Orders**: No cash check (leverage assumed)
- **CNC Orders**: Require `cash_balance >= (qty * executed_price + fees)`

### Position Updates

Positions use weighted average pricing:

```
new_avg_price = (current_qty * current_avg + fill_qty * fill_price) / (current_qty + fill_qty)
```

## Error Codes

- `ACCOUNT_NOT_FOUND`: Paper account doesn't exist
- `INSUFFICIENT_CASH`: Not enough cash for CNC order
- `INVALID_ORDER`: Order parameters are invalid
- `ORDER_NOT_FOUND`: Order doesn't exist
- `ORDER_NOT_OPEN`: Order cannot be modified/cancelled

## Curl Examples

### Create Account
```bash
curl -X POST "http://localhost:8000/paper/account/create" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"starting_cash": 100000}'
```

### Place Market Order
```bash
curl -X POST "http://localhost:8000/paper/orders" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "BUY",
    "qty": 10,
    "order_type": "MARKET",
    "product": "MIS"
  }'
```

### Place Limit Order
```bash
curl -X POST "http://localhost:8000/paper/orders" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "side": "BUY",
    "qty": 10,
    "order_type": "LIMIT",
    "limit_price": 150.00,
    "product": "CNC"
  }'
```

### List Orders
```bash
curl -X GET "http://localhost:8000/paper/orders?status=FILLED" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Cancel Order
```bash
curl -X POST "http://localhost:8000/paper/orders/123e4567-e89b-12d3-a456-426614174000/cancel" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Positions
```bash
curl -X GET "http://localhost:8000/paper/positions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Schema

### paper_accounts
- `id`: Primary key
- `user_id`: Foreign key to users
- `currency`: Account currency
- `starting_cash`: Initial cash amount
- `cash_balance`: Current cash balance

### paper_orders
- `id`: UUID primary key
- `account_id`: Foreign key to paper_accounts
- `symbol`: Trading symbol
- `side`: BUY/SELL
- `qty`: Order quantity
- `order_type`: MARKET/LIMIT
- `limit_price`: Limit price (nullable)
- `status`: Order status
- `product`: MIS/CNC
- `tif`: DAY (time in force)

### paper_fills
- `id`: Primary key
- `order_id`: Foreign key to paper_orders
- `symbol`: Trading symbol
- `qty`: Filled quantity
- `price`: Execution price
- `fees`: Trading fees
- `slippage`: Applied slippage

### paper_positions
- `id`: Primary key
- `account_id`: Foreign key to paper_accounts
- `symbol`: Trading symbol
- `product`: MIS/CNC
- `net_qty`: Net position quantity
- `avg_price`: Average price
- `realized_pnl`: Realized profit/loss

### paper_ledger
- `id`: Primary key
- `account_id`: Foreign key to paper_accounts
- `type`: TRADE/FEE/DEPOSIT/WITHDRAW
- `amount`: Transaction amount
- `meta`: JSON metadata
- `ts`: Timestamp

## Running Tests

```bash
# Run paper execution tests
pytest backend/tests/test_paper_execution_flow.py -v

# Run all tests
pytest
```

## Migration

```bash
# Apply migrations
alembic upgrade head

# Create new migration (if schema changes)
alembic revision --autogenerate -m "Update paper trading schema"
```

## Starting the Server

```bash
# Development
uvicorn backend.app.main:app --reload

# Production
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Integration with Strategies

Strategies can use the broker interface to switch between paper and live execution:

```python
from backend.execution.broker_interface import BrokerInterface

# For paper trading
broker = PaperBroker(db_session)

# For live trading (future)
# broker = LiveBroker(api_key, api_secret)

# Strategy code remains the same
order = broker.place_order(user_id, order_request)
positions = broker.get_positions(user_id)
