from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.enums import RiskAction, RiskEventType
from backend.app.models import RiskEvent, RiskLimit
from backend.app.risk_engine.types import RiskSnapshot

DEFAULT_LIMIT_FIELDS = [
    "daily_loss_inr",
    "daily_loss_pct",
    "max_position_value_inr",
    "max_position_qty",
    "max_gross_exposure_inr",
    "max_net_exposure_inr",
    "max_open_orders",
    "cutoff_time",
    "is_enabled",
    "is_halted",
    "halted_reason",
]


class RiskService:
    """
    Risk persistence and configuration resolver.
    """

    def __init__(self, db: Session):
        self.db = db

    def _default_limits(self) -> dict:
        return {
            "daily_loss_inr": Decimal(settings.max_daily_loss_inr),
            "daily_loss_pct": Decimal(settings.max_daily_loss_pct),
            "max_position_value_inr": Decimal(settings.max_position_value_inr),
            "max_position_qty": int(settings.max_position_qty),
            "max_gross_exposure_inr": Decimal(settings.max_gross_exposure_inr),
            "max_net_exposure_inr": Decimal(settings.max_net_exposure_inr),
            "max_open_orders": int(settings.max_open_orders),
            "cutoff_time": settings.cutoff_time,
            "is_enabled": bool(settings.enable_risk_enforcement),
            "is_halted": False,
            "halted_reason": None,
        }

    def get_effective_limits(self, user_id: int, strategy_id: Optional[str] = None) -> RiskLimit:
        """
        Merge limits in order: defaults -> user -> strategy.
        """
        merged = self._default_limits()

        user_limits = (
            self.db.query(RiskLimit)
            .filter(RiskLimit.user_id == user_id, RiskLimit.strategy_id.is_(None))
            .first()
        )
        strategy_limits = (
            self.db.query(RiskLimit)
            .filter(RiskLimit.user_id == user_id, RiskLimit.strategy_id == strategy_id)
            .first()
        )

        for limit_record in (user_limits, strategy_limits):
            if not limit_record:
                continue
            for field in DEFAULT_LIMIT_FIELDS:
                value = getattr(limit_record, field, None)
                if value is not None:
                    merged[field] = value

        return RiskLimit(**merged, user_id=user_id, strategy_id=strategy_id)

    def upsert_limits(self, user_id: int, payload: dict, strategy_id: Optional[str] = None) -> RiskLimit:
        limits = (
            self.db.query(RiskLimit)
            .filter(RiskLimit.user_id == user_id, RiskLimit.strategy_id == strategy_id)
            .first()
        )
        if not limits:
            limits = RiskLimit(user_id=user_id, strategy_id=strategy_id)
            self.db.add(limits)

        for key, value in payload.items():
            if hasattr(limits, key):
                setattr(limits, key, value)

        self.db.commit()
        self.db.refresh(limits)
        return limits

    def log_event(
        self,
        user_id: int,
        event_type: RiskEventType,
        reason_code: str,
        message: str,
        snapshot: RiskSnapshot,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> RiskEvent:
        event = RiskEvent(
            user_id=user_id,
            strategy_id=strategy_id,
            symbol=symbol,
            event_type=event_type,
            reason_code=reason_code,
            message=message,
            snapshot=snapshot.model_dump(mode="json"),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def set_halt(self, user_id: int, halted: bool, reason: str, strategy_id: Optional[str] = None) -> RiskLimit:
        limits = (
            self.db.query(RiskLimit)
            .filter(RiskLimit.user_id == user_id, RiskLimit.strategy_id == strategy_id)
            .first()
        )
        if not limits:
            limits = RiskLimit(user_id=user_id, strategy_id=strategy_id)
            self.db.add(limits)

        limits.is_halted = halted
        limits.halted_reason = reason
        self.db.commit()
        self.db.refresh(limits)
        return limits


__all__ = ["RiskService"]
