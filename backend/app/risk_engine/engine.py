from backend.app.enums import RiskAction
from backend.app.risk_engine import rules
from backend.app.risk_engine.types import OrderIntent, RiskDecision, RiskSnapshot
from backend.app.models import RiskLimit


def run_all_rules(order_intent: OrderIntent, snapshot: RiskSnapshot, limits: RiskLimit) -> RiskDecision:
    """
    Run all risk rules in deterministic order and return the first blocking decision.
    """
    rule_checks = [
        rules.rule_kill_switch_if_halted(snapshot, limits),
        rules.rule_cutoff_time(snapshot, limits, order_intent),
        rules.rule_price_sanity(order_intent),
        rules.rule_max_open_orders(snapshot, limits, order_intent),
        rules.rule_max_daily_loss_inr(snapshot, limits),
        rules.rule_max_daily_loss_pct(snapshot, limits),
        rules.rule_max_position_qty(snapshot, limits, order_intent),
        rules.rule_max_position_value(snapshot, limits, order_intent),
        rules.rule_max_gross_exposure(snapshot, limits, order_intent),
        rules.rule_max_net_exposure(snapshot, limits, order_intent),
        rules.rule_cash_check(snapshot, limits, order_intent),
    ]

    for decision in rule_checks:
        if decision:
            return decision

    return RiskDecision(
        action=RiskAction.ALLOW,
        reason_code="ALLOWED",
        message="Order is allowed.",
    )
