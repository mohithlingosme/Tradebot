"""Background billing tasks."""

from datetime import datetime, timedelta

from sqlmodel import Session, select

from ..database import engine
from .models import Invoice, Plan, Subscription


def generate_nightly_invoices() -> None:
    """Issue invoices for active subscriptions."""
    with Session(engine) as session:
        subscriptions = session.exec(select(Subscription).where(Subscription.status == "active")).all()
        for sub in subscriptions:
            plan = session.get(Plan, sub.plan_id)
            if not plan:
                continue
            invoice = Invoice(subscription_id=sub.id, amount_inr=plan.price_inr, status="issued")
            session.add(invoice)
            sub.current_period_end = datetime.utcnow() + timedelta(days=30)
        session.commit()
