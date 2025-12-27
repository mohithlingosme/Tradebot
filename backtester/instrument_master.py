"""
Instrument Master for Backtesting

Manages instrument metadata including symbol mappings, lot sizes,
expiry dates, and other instrument-specific information.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class Instrument:
    """Represents a financial instrument."""
    symbol: str
    name: str
    instrument_type: str  # 'cash', 'futures', 'options', 'index'
    exchange: str = "NSE"
    lot_size: int = 1
    tick_size: float = 0.01
    expiry_date: Optional[datetime] = None
    strike_price: Optional[float] = None
    option_type: Optional[str] = None  # 'CE' or 'PE'
    underlying_symbol: Optional[str] = None
    sector: Optional[str] = None
    is_active: bool = True

    def is_expired(self, current_date: datetime) -> bool:
        """Check if instrument is expired."""
        if self.expiry_date:
            return current_date > self.expiry_date
        return False


class InstrumentMaster:
    """Manages instrument metadata and mappings."""

    def __init__(self, data_dir: str = "data/instruments"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.instruments: Dict[str, Instrument] = {}
        self.symbol_mappings: Dict[str, str] = {}  # alias -> canonical symbol

        # Load existing data
        self._load_instruments()

    def add_instrument(self, instrument: Instrument) -> None:
        """Add or update an instrument."""
        self.instruments[instrument.symbol] = instrument
        logger.info(f"Added instrument: {instrument.symbol}")

    def get_instrument(self, symbol: str) -> Optional[Instrument]:
        """Get instrument by symbol."""
        # Check direct symbol
        if symbol in self.instruments:
            return self.instruments[symbol]

        # Check mappings
        canonical = self.symbol_mappings.get(symbol)
        if canonical and canonical in self.instruments:
            return self.instruments[canonical]

        return None

    def add_symbol_mapping(self, alias: str, canonical_symbol: str) -> None:
        """Add symbol alias mapping."""
        self.symbol_mappings[alias] = canonical_symbol
        logger.info(f"Added mapping: {alias} -> {canonical_symbol}")

    def get_active_instruments(self, instrument_type: Optional[str] = None) -> List[Instrument]:
        """Get list of active instruments, optionally filtered by type."""
        instruments = [inst for inst in self.instruments.values() if inst.is_active]

        if instrument_type:
            instruments = [inst for inst in instruments if inst.instrument_type == instrument_type]

        return instruments

    def get_expiring_instruments(self, current_date: datetime, days_ahead: int = 30) -> List[Instrument]:
        """Get instruments expiring within specified days."""
        from datetime import timedelta

        cutoff_date = current_date + timedelta(days=days_ahead)
        expiring = []

        for instrument in self.instruments.values():
            if (instrument.expiry_date and
                current_date <= instrument.expiry_date <= cutoff_date):
                expiring.append(instrument)

        return expiring

    def _load_instruments(self) -> None:
        """Load instruments from storage."""
        instruments_file = self.data_dir / "instruments.json"
        mappings_file = self.data_dir / "mappings.json"

        if instruments_file.exists():
            try:
                with open(instruments_file, 'r') as f:
                    data = json.load(f)
                    for symbol, inst_data in data.items():
                        # Convert expiry_date string back to datetime
                        if inst_data.get('expiry_date'):
                            inst_data['expiry_date'] = datetime.fromisoformat(inst_data['expiry_date'])
                        self.instruments[symbol] = Instrument(**inst_data)
                logger.info(f"Loaded {len(self.instruments)} instruments")
            except Exception as e:
                logger.error(f"Error loading instruments: {e}")

        if mappings_file.exists():
            try:
                with open(mappings_file, 'r') as f:
                    self.symbol_mappings = json.load(f)
                logger.info(f"Loaded {len(self.symbol_mappings)} symbol mappings")
            except Exception as e:
                logger.error(f"Error loading mappings: {e}")

    def save_instruments(self) -> None:
        """Save instruments to storage."""
        instruments_file = self.data_dir / "instruments.json"
        mappings_file = self.data_dir / "mappings.json"

        # Convert instruments to dict, handling datetime
        instruments_data = {}
        for symbol, inst in self.instruments.items():
            inst_dict = {
                'symbol': inst.symbol,
                'name': inst.name,
                'instrument_type': inst.instrument_type,
                'exchange': inst.exchange,
                'lot_size': inst.lot_size,
                'tick_size': inst.tick_size,
                'strike_price': inst.strike_price,
                'option_type': inst.option_type,
                'underlying_symbol': inst.underlying_symbol,
                'sector': inst.sector,
                'is_active': inst.is_active
            }
            if inst.expiry_date:
                inst_dict['expiry_date'] = inst.expiry_date.isoformat()
            instruments_data[symbol] = inst_dict

        try:
            with open(instruments_file, 'w') as f:
                json.dump(instruments_data, f, indent=2)
            logger.info(f"Saved {len(self.instruments)} instruments")
        except Exception as e:
            logger.error(f"Error saving instruments: {e}")

        try:
            with open(mappings_file, 'w') as f:
                json.dump(self.symbol_mappings, f, indent=2)
            logger.info(f"Saved {len(self.symbol_mappings)} mappings")
        except Exception as e:
            logger.error(f"Error saving mappings: {e}")

    def initialize_nse_instruments(self) -> None:
        """Initialize with common NSE instruments for MVP."""
        # Cash equities
        cash_instruments = [
            Instrument("RELIANCE", "Reliance Industries Ltd", "cash", lot_size=1),
            Instrument("TCS", "Tata Consultancy Services Ltd", "cash", lot_size=1),
            Instrument("HDFCBANK", "HDFC Bank Ltd", "cash", lot_size=1),
            Instrument("ICICIBANK", "ICICI Bank Ltd", "cash", lot_size=1),
            Instrument("INFY", "Infosys Ltd", "cash", lot_size=1),
            Instrument("HINDUNILVR", "Hindustan Unilever Ltd", "cash", lot_size=1),
        ]

        # Indices
        index_instruments = [
            Instrument("NIFTY50", "NIFTY 50 Index", "index", lot_size=50),
            Instrument("BANKNIFTY", "NIFTY Bank Index", "index", lot_size=25),
        ]

        # Futures (example - would need dynamic expiry management)
        futures_instruments = [
            Instrument("RELIANCE24JANFUT", "Reliance Industries Jan 2024 Futures",
                      "futures", lot_size=250, underlying_symbol="RELIANCE",
                      expiry_date=datetime(2024, 1, 25)),
        ]

        all_instruments = cash_instruments + index_instruments + futures_instruments

        for inst in all_instruments:
            self.add_instrument(inst)

        # Add some common mappings
        self.add_symbol_mapping("NIFTY", "NIFTY50")
        self.add_symbol_mapping("BANKNIFTY", "BANKNIFTY")

        self.save_instruments()
        logger.info("Initialized NSE instruments")


# Example usage
if __name__ == "__main__":
    master = InstrumentMaster()
    master.initialize_nse_instruments()

    # Get an instrument
    reliance = master.get_instrument("RELIANCE")
    if reliance:
        print(f"RELIANCE: {reliance.name}, Lot size: {reliance.lot_size}")

    # Get active cash instruments
    cash = master.get_active_instruments("cash")
    print(f"Active cash instruments: {len(cash)}")
