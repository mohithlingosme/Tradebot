from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
from ..schemas.paper import PaperOrderRequest, PaperOrderResponse, PaperPositionResponse


class BrokerInterface(ABC):
    """Abstract base class for broker implementations (paper/live)."""

    @abstractmethod
    def place_order(self, user_id: int, order_request: PaperOrderRequest) -> PaperOrderResponse:
        """Place an order."""
        pass

    @abstractmethod
    def cancel_order(self, user_id: int, order_id: str) -> bool:
        """Cancel an order."""
        pass

    @abstractmethod
    def get_positions(self, user_id: int) -> List[PaperPositionResponse]:
        """Get current positions."""
        pass

    @abstractmethod
    def get_account_balance(self, user_id: int) -> Optional[Decimal]:
        """Get account balance."""
        pass
