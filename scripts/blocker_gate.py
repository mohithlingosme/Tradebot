"""Fail CI if critical issues are still open."""

from __future__ import annotations

import os
import sys

import requests

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY", "finbot/finbot")
LABEL = "priority:critical"


def fetch_blockers() -> list[dict]:
    url = f"https://api.github.com/repos/{REPO}/issues"
    params = {"state": "open", "labels": LABEL}
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def main() -> None:
    blockers = fetch_blockers()
    if blockers:
        print("Blocking issues detected:")
        for issue in blockers:
            print(f"- {issue['title']} ({issue['html_url']})")
        sys.exit(1)
    print("No blocking issues.")


if __name__ == "__main__":
    main()
