from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

from trading_engine.phase4.models import OrderSide


class InstrumentType(Enum):
    CASH = "cash"
    FUTURES = "futures"
    OPTIONS = "options"
    INDEX = "index"


@dataclass
class IndiaFeeConfig:
    """India-specific fee configuration for NSE."""

    # Brokerage rates (per order)
    brokerage: Dict[str, float] = None

    # Securities Transaction Tax
    stt: Dict[str, float] = None

    # Exchange Transaction Charge
    exchange_tx_charge: Dict[str, float] = None

    # GST on brokerage + exchange charges
    gst: float = 0.18

    # Stamp Duty
    stamp_duty: Dict[str, float] = None

    # SEBI Turnover Fee
    sebi_fee: float = 0.0000005

    def __post_init__(self):
        if self.brokerage is None:
            self.brokerage = {
                "equity_cash": 0.0003,  # 0.03%
                "equity_futures": 0.0002,  # 0.02%
                "equity_options": 0.0005,  # 0.05%
                "currency_futures": 0.00015,  # 0.015%
                "currency_options": 0.0004,  # 0.04%
            }

        if self.stt is None:
            self.stt = {
                "equity_delivery": 0.001,  # 0.1%
                "equity_intraday": 0.00025,  # 0.025%
                "futures": 0.0001,  # 0.01%
                "options": 0.000125,  # 0.0125%
            }

        if self.exchange_tx_charge is None:
            self.exchange_tx_charge = {
                "equity": 0.0000325,  # 0.00325%
                "futures": 0.00019,  # 0.019%
                "options": 0.00053,  # 0.053%
            }

        if self.stamp_duty is None:
            self.stamp_duty = {
                "equity_delivery": 0.00015,  # 0.015%
                "equity_intraday": 0.00003,  # 0.003%
                "futures_options": 0.00002,  # 0.002%
            }


@dataclass
class CostModel:
    """Enhanced cost model with India-specific fees and slippage."""

    # Slippage
    slippage_bps: float = 1.0

    # Legacy simple fees (for backward compatibility)
    commission_rate: float = 0.0005
    fee_per_order: float = 0.0
    fee_per_unit: float = 0.0

    # India-specific configuration
    india_fees: IndiaFeeConfig = None

    def __post_init__(self):
        if self.india_fees is None:
            self.india_fees = IndiaFeeConfig()

    def price_with_slippage(self, side: OrderSide, price: float) -> float:
        """Apply slippage to price."""
        if price <= 0:
            return price
        slip = (self.slippage_bps / 10_000) * price
        if side == OrderSide.BUY:
            return price + slip
        return price - slip

    def calculate_india_fees(self, instrument_type: str, trade_value: float,
                           is_delivery: bool = False, is_intraday: bool = True) -> Dict[str, float]:
        """
        Calculate comprehensive India trading fees.

        Args:
            instrument_type: 'cash', 'futures', 'options', 'index'
            trade_value: Absolute value of the trade
            is_delivery: Whether it's a delivery trade (for equity)
            is_intraday: Whether it's intraday (for STT calculation)

        Returns:
            Dict of fee components
        """
        fees = {}

        # 1. Brokerage
        if instrument_type == "cash":
            fees['brokerage'] = min(trade_value * self.india_fees.brokerage["equity_cash"], 20.0)
        elif instrument_type == "futures":
            fees['brokerage'] = min(trade_value * self.india_fees.brokerage["equity_futures"], 20.0)
        elif instrument_type == "options":
            fees['brokerage'] = min(trade_value * self.india_fees.brokerage["equity_options"], 20.0)
        else:
            fees['brokerage'] = 0.0

        # 2. STT (Securities Transaction Tax)
        if instrument_type == "cash":
            if is_delivery:
                fees['stt'] = trade_value * self.india_fees.stt["equity_delivery"]
            else:
                fees['stt'] = trade_value * self.india_fees.stt["equity_intraday"]
        elif instrument_type in ["futures", "options"]:
            if instrument_type == "futures":
                fees['stt'] = trade_value * self.india_fees.stt["futures"]
            else:
                fees['stt'] = trade_value * self.india_fees.stt["options"]

        # 3. Exchange Transaction Charge
        if instrument_type == "cash":
            fees['exchange_tx'] = trade_value * self.india_fees.exchange_tx_charge["equity"]
        elif instrument_type == "futures":
            fees['exchange_tx'] = trade_value * self.india_fees.exchange_tx_charge["futures"]
        elif instrument_type == "options":
            fees['exchange_tx'] = trade_value * self.india_fees.exchange_tx_charge["options"]

        # 4. GST on (brokerage + exchange_tx)
        gst_base = fees['brokerage'] + fees.get('exchange_tx', 0)
        fees['gst'] = gst_base * self.india_fees.gst

        # 5. Stamp Duty
        if instrument_type == "cash":
            if is_delivery:
                fees['stamp_duty'] = trade_value * self.india_fees.stamp_duty["equity_delivery"]
            else:
                fees['stamp_duty'] = trade_value * self.india_fees.stamp_duty["equity_intraday"]
        elif instrument_type in ["futures", "options"]:
            fees['stamp_duty'] = trade_value * self.india_fees.stamp_duty["futures_options"]

        # 6. SEBI Turnover Fee
        fees['sebi_fee'] = trade_value * self.india_fees.sebi_fee

        return fees

    def total_fees_india(self, instrument_type: str, trade_value: float,
                        is_delivery: bool = False, is_intraday: bool = True) -> float:
        """Calculate total India fees for a trade."""
        fee_components = self.calculate_india_fees(instrument_type, trade_value, is_delivery, is_intraday)
        return sum(fee_components.values())

    # Legacy methods for backward compatibility
    def commission(self, price: float, quantity: float) -> float:
        """Legacy commission calculation."""
        return max(price * quantity * self.commission_rate, 0.0)

    def extra_fees(self, quantity: float) -> float:
        """Legacy extra fees."""
        return max(self.fee_per_order + self.fee_per_unit * quantity, 0.0)

    def total_fees(self, price: float, quantity: float) -> float:
        """Legacy total fees."""
        return self.commission(price, quantity) + self.extra_fees(quantity)
