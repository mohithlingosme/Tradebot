from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.auth import get_current_user
from backend.app.database import get_db
from backend.app.models import RiskEvent, User
from backend.app.schemas.risk import HaltRequest, RiskEventResponse, RiskLimitUpdate, RiskStatusResponse
from backend.app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["risk"])


def _risk_service(db: Session) -> RiskService:
    return RiskService(db)


@router.get("/limits", response_model=dict)
async def get_risk_limits(
    strategy_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = _risk_service(db)
    limits = svc.get_effective_limits(current_user.id, strategy_id)
    return {
        "daily_loss_inr": limits.daily_loss_inr,
        "daily_loss_pct": limits.daily_loss_pct,
        "max_position_value_inr": limits.max_position_value_inr,
        "max_position_qty": limits.max_position_qty,
        "max_gross_exposure_inr": limits.max_gross_exposure_inr,
        "max_net_exposure_inr": limits.max_net_exposure_inr,
        "max_open_orders": limits.max_open_orders,
        "cutoff_time": limits.cutoff_time,
        "is_enabled": limits.is_enabled,
        "is_halted": limits.is_halted,
        "halted_reason": limits.halted_reason,
    }


@router.put("/limits", response_model=dict)
async def update_risk_limits(
    limits: RiskLimitUpdate,
    strategy_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = _risk_service(db)
    updated_limits = svc.upsert_limits(current_user.id, limits.model_dump(exclude_unset=True), strategy_id)
    return {
        "daily_loss_inr": updated_limits.daily_loss_inr,
        "daily_loss_pct": updated_limits.daily_loss_pct,
        "max_position_value_inr": updated_limits.max_position_value_inr,
        "max_position_qty": updated_limits.max_position_qty,
        "max_gross_exposure_inr": updated_limits.max_gross_exposure_inr,
        "max_net_exposure_inr": updated_limits.max_net_exposure_inr,
        "max_open_orders": updated_limits.max_open_orders,
        "cutoff_time": updated_limits.cutoff_time,
        "is_enabled": updated_limits.is_enabled,
        "is_halted": updated_limits.is_halted,
        "halted_reason": updated_limits.halted_reason,
    }


@router.get("/status", response_model=RiskStatusResponse)
async def get_risk_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = _risk_service(db)
    limits = svc.get_effective_limits(current_user.id)
    return RiskStatusResponse(
        is_enabled=limits.is_enabled,
        is_halted=limits.is_halted,
        halted_reason=limits.halted_reason,
        last_updated=limits.updated_at,
    )


@router.post("/halt")
async def halt_trading(
    request: HaltRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = _risk_service(db)
    svc.set_halt(current_user.id, True, request.reason)
    return {"message": "Trading halted", "reason": request.reason}


@router.post("/resume")
async def resume_trading(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc = _risk_service(db)
    svc.set_halt(current_user.id, False, "")
    return {"message": "Trading resumed"}


@router.get("/events", response_model=List[RiskEventResponse])
async def get_risk_events(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    events_query = db.query(RiskEvent).filter(RiskEvent.user_id == current_user.id)
    if from_date:
        events_query = events_query.filter(RiskEvent.ts >= from_date)
    if to_date:
        events_query = events_query.filter(RiskEvent.ts <= to_date)

    events = events_query.order_by(RiskEvent.ts.desc()).limit(limit).offset(offset).all()
    return events
