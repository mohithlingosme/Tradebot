#!/usr/bin/env python3
"""
Finbot safety audit script.

Runs pre-flight checks before enabling live/public modes.
Intended to be invoked manually or in CI/CD (e.g., before PROD deploy).
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Iterable, List, Tuple


def read_env(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def normalize_mode(
    value: str | None,
    *,
    default: str = "dev",
    allowed: Iterable[str] | None = ("dev", "paper", "live"),
) -> str:
    """Normalize textual mode strings with optional clamping to known values."""
    if value is None:
        return default
    normalized = value.strip().lower()
    if allowed:
        allowed_set = {item.lower() for item in allowed}
        if normalized not in allowed_set:
            return default
    return normalized


def check_trading_mode() -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    criticals: List[str] = []

    trading_mode = normalize_mode(
        read_env("TRADING_MODE") or read_env("FINBOT_MODE"),
        default="unknown",
        allowed=("dev", "paper", "live"),
    )
    environment = normalize_mode(
        read_env("ENVIRONMENT") or read_env("APP_ENV"),
        default="unknown",
        allowed=None,
    )
    live_confirm = (read_env("FINBOT_LIVE_TRADING_CONFIRM") or "").strip().lower() in {"true", "1", "yes"}

    if trading_mode == "unknown":
        warnings.append("TRADING_MODE not set; defaulting is risky. Set TRADING_MODE=DEV/PAPER/LIVE explicitly.")
    elif trading_mode == "live":
        criticals.append("⚠ LIVE TRADING MODE ENABLED. Confirm SEBI/compliance approvals and risk controls.")
        if not live_confirm:
            criticals.append("FINBOT_LIVE_TRADING_CONFIRM is not true while TRADING_MODE=LIVE.")
    elif trading_mode in {"dev", "paper"}:
        warnings.append(f"TRADING_MODE={trading_mode.upper()}: good for non-production validation.")

    if environment in {"prod", "production"} and trading_mode != "live":
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

    trading_mode = normalize_mode(
        read_env("TRADING_MODE") or read_env("FINBOT_MODE"),
        default="unknown",
        allowed=("dev", "paper", "live"),
    )
    environment = normalize_mode(
        read_env("ENVIRONMENT") or read_env("APP_ENV"),
        default="unknown",
        allowed=None,
    )
    live_context = trading_mode == "live" or environment in {"prod", "production"}

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

    use_case = normalize_mode(
        read_env("APP_USE_CASE") or "PERSONAL_EXPERIMENTAL",
        default="personal_experimental",
        allowed=None,
    )
    trading_mode = normalize_mode(
        read_env("TRADING_MODE") or read_env("FINBOT_MODE"),
        default="unknown",
        allowed=("dev", "paper", "live"),
    )

    if use_case not in {"personal_experimental", "internal_only", "public_distribution"}:
        warnings.append(f"APP_USE_CASE={use_case.upper()} is unknown; default is PERSONAL_EXPERIMENTAL.")

    if use_case == "public_distribution":
        criticals.append(
            "APP_USE_CASE=PUBLIC_DISTRIBUTION set. Legal/regulatory review required before any client-facing use."
        )

    if trading_mode == "live" and use_case != "personal_experimental":
        criticals.append(
            f"TRADING_MODE=LIVE with APP_USE_CASE={use_case.upper()}. Confirm SEBI/compliance approvals before proceeding."
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
