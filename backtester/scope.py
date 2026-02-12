"""
Backtesting Scope and Rules Definitions

This module defines the core assumptions and rules for the backtesting system,
focusing on NSE (India) markets.
"""

from enum import Enum
from typing import List, Set


class InstrumentType(Enum):
    """Supported instrument types for backtesting."""
    CASH = "cash"  # Equity cash market
    FUTURES = "futures"  # Futures contracts
    OPTIONS = "options"  # Options contracts
    INDICES = "indices"  # Index instruments


class Timeframe(Enum):
    """Supported timeframes for backtesting."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    DAILY = "1d"


class OrderType(Enum):
    """Order types supported in MVP."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_MARKET = "stop_loss_market"


class FillModel(Enum):
    """Fill model assumptions."""
    NEXT_BAR_OPEN = "next_bar_open"  # Fill at next bar's open price
    NEXT_TICK = "next_tick"  # Fill at next tick (if tick data available)
    MID_PRICE = "mid"  # Fill at mid of bid/ask
    BID_ASK = "bid_ask"  # Fill at bid for sell, ask for buy


# Instrument Universe
SUPPORTED_INSTRUMENTS: Set[InstrumentType] = {
    InstrumentType.CASH,
    InstrumentType.FUTURES,
    InstrumentType.OPTIONS,
    InstrumentType.INDICES,
}

# Timeframes
SUPPORTED_TIMEFRAMES: Set[Timeframe] = {
    Timeframe.MINUTE_1,
    Timeframe.MINUTE_5,
    Timeframe.MINUTE_15,
    Timeframe.DAILY,
}

# Orders
SUPPORTED_ORDERS: Set[OrderType] = {
    OrderType.MARKET,
    OrderType.LIMIT,
    OrderType.STOP_LOSS,
    OrderType.STOP_LOSS_MARKET,
}

# Fill Model (MVP default)
DEFAULT_FILL_MODEL = FillModel.NEXT_BAR_OPEN

# Trading Session Rules (NSE)
NSE_MARKET_OPEN = "09:15"  # IST
NSE_MARKET_CLOSE = "15:30"  # IST
NSE_TIMEZONE = "Asia/Kolkata"

# Holidays (simplified - in production, use a proper calendar library)
NSE_HOLIDAYS_2024 = [
    "2024-01-01",  # New Year
    "2024-01-26",  # Republic Day
    "2024-03-08",  # Holi
    "2024-03-25",  # Good Friday
    "2024-03-29",  # Mahavir Jayanti
    "2024-04-11",  # Id-ul-Fitr
    "2024-04-17",  # Ram Navmi
    "2024-05-01",  # Labour Day
    "2024-08-15",  # Independence Day
    "2024-08-26",  # Krishna Janmashtami
    "2024-10-02",  # Gandhi Jayanti
    "2024-10-12",  # Dussehra
    "2024-11-01",  # Diwali
    "2024-12-25",  # Christmas
]

# Fees and Taxes Model (India - NSE)
# These are approximate and should be configurable
DEFAULT_FEES_CONFIG = {
    "brokerage": {
        "equity_cash": 0.0003,  # 0.03% or min Rs. 20
        "equity_futures": 0.0002,  # 0.02% or min Rs. 20
        "equity_options": 0.0005,  # 0.05% or min Rs. 20
        "currency_futures": 0.00015,  # 0.015%
        "currency_options": 0.0004,  # 0.04%
    },
    "stt": {  # Securities Transaction Tax
        "equity_delivery": 0.001,  # 0.1%
        "equity_intraday": 0.00025,  # 0.025%
        "futures": 0.0001,  # 0.01%
        "options": 0.000125,  # 0.0125%
    },
    "exchange_transaction_charge": {
        "equity": 0.0000325,  # 0.00325%
        "futures": 0.00019,  # 0.019%
        "options": 0.00053,  # 0.053%
    },
    "gst": 0.18,  # 18% on brokerage + exchange charges
    "stamp_duty": {
        "equity_delivery": 0.00015,  # 0.015%
        "equity_intraday": 0.00003,  # 0.003%
        "futures_options": 0.00002,  # 0.002%
    },
    "sebi_turnover_fee": 0.0000005,  # 0.00005%
}

# Slippage Model
DEFAULT_SLIPPAGE_BPS = 1.0  # 1 basis point

# Corporate Actions (MVP - basic splits)
SUPPORT_CORPORATE_ACTIONS = True
