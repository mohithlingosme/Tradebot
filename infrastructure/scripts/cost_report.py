"""Generate AWS cost report and post to Slack."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import boto3
import requests


def fetch_costs() -> dict:
    client = boto3.client("ce", region_name="us-east-1")
    end = datetime.utcnow().date()
    start = end - timedelta(days=7)
    data = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    return data


def format_message(costs: dict) -> str:
    rows = costs["ResultsByTime"]
    lines = ["Weekly AWS Spend"]
    for row in rows:
        amount = row["Total"]["UnblendedCost"]["Amount"]
        date = row["TimePeriod"]["Start"]
        lines.append(f"- {date}: ${float(amount):.2f} USD")
    return "\n".join(lines)


def post_to_slack(message: str) -> None:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print(message)
        return
    requests.post(webhook, json={"text": message}, timeout=10)


if __name__ == "__main__":
    report = fetch_costs()
    message = format_message(report)
    post_to_slack(message)
