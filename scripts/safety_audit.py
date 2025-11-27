#!/usr/bin/env python3
"""
Finbot safety audit script.

Runs pre-flight checks before enabling live/public modes.
Intended to be invoked manually or in CI/CD (e.g., before PROD deploy).
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple


def read_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def normalize_mode(value: str | None) -> str:
    if not value:
        return "UNKNOWN"
    return value.strip().upper()


def check_trading_mode() -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    criticals: List[str] = []

    trading_mode = normalize_mode(read_env("TRADING_MODE") or read_env("FINBOT_MODE"))
    environment = normalize_mode(read_env("ENVIRONMENT") or read_env("APP_ENV"))
    live_confirm = normalize_mode(read_env("FINBOT_LIVE_TRADING_CONFIRM")) in {"TRUE", "1", "YES"}

    if trading_mode == "UNKNOWN":
        warnings.append("TRADING_MODE not set; defaulting is risky. Set TRADING_MODE=DEV/PAPER/LIVE explicitly.")
    elif trading_mode == "LIVE":
        criticals.append("⚠ LIVE TRADING MODE ENABLED. Confirm SEBI/compliance approvals and risk controls.")
        if not live_confirm:
            criticals.append("FINBOT_LIVE_TRADING_CONFIRM is not true while TRADING_MODE=LIVE.")
    elif trading_mode in {"DEV", "PAPER", "DEMO"}:
        warnings.append(f"TRADING_MODE={trading_mode}: good for non-production validation.")

    if environment in {"PROD", "PRODUCTION"} and trading_mode != "LIVE":
        warnings.append("APP_ENV/ENVIRONMENT=PRODUCTION but TRADING_MODE is not LIVE; ensure this is intentional.")

    return warnings, criticals


def looks_like_placeholder(value: str) -> bool:
    lower = value.lower()
    return any(tag in lower for tag in ["demo", "test", "changeme", "placeholder", "sample", "example"])


def check_api_keys() -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    criticals: List[str] = []

    key_names = [
        "BROKER_API_KEY",
        "BROKER_API_SECRET",
        "DATA_API_KEY",
        "ALPHAVANTAGE_API_KEY",
        "KITE_API_KEY",
        "KITE_API_SECRET",
    ]

    trading_mode = normalize_mode(read_env("TRADING_MODE") or read_env("FINBOT_MODE"))
    environment = normalize_mode(read_env("ENVIRONMENT") or read_env("APP_ENV"))
    live_context = trading_mode == "LIVE" or environment in {"PROD", "PRODUCTION"}

    for key in key_names:
        value = read_env(key)
        if not value:
            warnings.append(f"{key} not set.")
            continue

        if looks_like_placeholder(value):
            warnings.append(f"{key} looks like a test/demo key.")
        elif live_context:
            criticals.append(f"⚠ {key} present while in LIVE/PROD context. Confirm approvals and risk controls.")

    return warnings, criticals


def check_use_case() -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    criticals: List[str] = []

    use_case = normalize_mode(read_env("APP_USE_CASE") or "PERSONAL_EXPERIMENTAL")
    trading_mode = normalize_mode(read_env("TRADING_MODE") or read_env("FINBOT_MODE"))

    if use_case not in {"PERSONAL_EXPERIMENTAL", "INTERNAL_ONLY", "PUBLIC_DISTRIBUTION"}:
        warnings.append(f"APP_USE_CASE={use_case} is unknown; default is PERSONAL_EXPERIMENTAL.")

    if use_case == "PUBLIC_DISTRIBUTION":
        criticals.append(
            "APP_USE_CASE=PUBLIC_DISTRIBUTION set. Legal/regulatory review required before any client-facing use."
        )

    if trading_mode == "LIVE" and use_case != "PERSONAL_EXPERIMENTAL":
        criticals.append(
            f"TRADING_MODE=LIVE with APP_USE_CASE={use_case}. Confirm SEBI/compliance approvals before proceeding."
        )

    return warnings, criticals


def print_summary_block() -> None:
    block = """
=====================================================
FINBOT SAFETY AUDIT – SUMMARY
-----------------------------------------------------
• This tool is experimental.
• It does NOT provide licensed investment advice.
• Trading in stocks and derivatives can result in large
  financial losses, including more than your initial capital.
• Use PAPER mode first and validate all logic.
• Consult a SEBI-registered investment adviser or
  qualified professional before relying on any outputs.
=====================================================
"""
    print(block.strip())


def main() -> int:
    warnings: List[str] = []
    criticals: List[str] = []

    for checker in (check_trading_mode, check_api_keys, check_use_case):
        w, c = checker()
        warnings.extend(w)
        criticals.extend(c)

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")

    if criticals:
        print("\nCritical issues:")
        for c in criticals:
            print(f"- {c}")

    print_summary_block()

    if criticals:
        print("Safety audit failed due to critical findings.")
        return 1

    print("Safety audit completed with warnings only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
