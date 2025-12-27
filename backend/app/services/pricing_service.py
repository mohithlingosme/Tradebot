from decimal import Decimal
from typing import Dict, Optional
from sqlalchemy.orm import Session
from ..models import Position


class PricingService:
    def __init__(self, db: Session):
        self.db = db

    def get_ltp(self, symbols: list[str]) -> Dict[str, Optional[Decimal]]:
        """
        Get Last Traded Price for symbols.
        For MVP, return mock prices or from position last_price if available.
        In production, integrate with real price feed.
        """
        prices = {}
        for symbol in symbols:
            # Mock LTP - in real implementation, fetch from price_history or live feed
            # For now, use a simple mock based on symbol
            mock_price = Decimal('100.00') + hash(symbol) % 100  # Simple hash-based mock
            prices[symbol] = mock_price
        return prices

    def get_ltp_single(self, symbol: str) -> Optional[Decimal]:
        """Get LTP for a single symbol."""
        prices = self.get_ltp([symbol])
        return prices.get(symbol)
