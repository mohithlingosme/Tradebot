from typing import List

from sqlalchemy.orm import Session

from .broker_interface import BrokerInterface
from ..schemas.paper import PaperOrderRequest, PaperOrderResponse, PaperPositionResponse
from ..services.paper_execution_service import PaperExecutionService
from ..config import settings


class PaperBroker(BrokerInterface):
    def __init__(self, db: Session):
        self.db = db
        self.execution_service = PaperExecutionService(db)

    def place_order(self, user_id: int, order_request: PaperOrderRequest) -> PaperOrderResponse:
        return self.execution_service.place_order(user_id, order_request)

    def get_positions(self, user_id: int) -> List[PaperPositionResponse]:
        return self.execution_service.get_positions(user_id)
