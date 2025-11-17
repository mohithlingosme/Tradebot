from __future__ import annotations

import hashlib
import hmac
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_session
from .models import Invoice, Plan, Subscription

router = APIRouter(prefix="/payments", tags=["payments"])


class CheckoutRequest(BaseModel):
    plan_id: int


class CheckoutResponse(BaseModel):
    order_id: str
    razorpay_key: str
    amount: int
    currency: str = "INR"


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_xxx")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "test_secret")


@router.post("/create-order", response_model=CheckoutResponse)
async def create_order(payload: CheckoutRequest, session: Session = Depends(get_session)):
    plan = session.query(Plan).filter(Plan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    order_id = f"order_{uuid4().hex}"
    amount_paise = plan.price_inr * 100

    return CheckoutResponse(order_id=order_id, razorpay_key=RAZORPAY_KEY_ID, amount=amount_paise)


def _verify_signature(body: bytes, received_signature: str) -> bool:
    digest = hmac.new(RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, received_signature)


@router.post("/webhook")
async def webhook(request: Request, session: Session = Depends(get_session)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature or not _verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    subscription_id = payload.get("payload", {}).get("subscription", {}).get("entity", {}).get("id")
    status = payload.get("payload", {}).get("subscription", {}).get("entity", {}).get("status")

    subscription = session.query(Subscription).filter(
        Subscription.razorpay_subscription_id == subscription_id
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription.status = status
    session.add(subscription)
    session.commit()
    return {"ok": True}


@router.post("/invoice/{subscription_id}")
async def generate_invoice(subscription_id: int, session: Session = Depends(get_session)):
    subscription = session.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    plan = session.query(Plan).filter(Plan.id == subscription.plan_id).first()
    invoice = Invoice(subscription_id=subscription.id, amount_inr=plan.price_inr, status="issued")
    session.add(invoice)
    session.commit()

    return {"invoice_id": invoice.id, "amount": invoice.amount_inr}
