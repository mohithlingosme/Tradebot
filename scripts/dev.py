"""Unified development helper commands.

Usage:
    python -m scripts.dev tests [-- <pytest args>]
    python -m scripts.dev lint
    python -m scripts.dev services [--services backend ingestion frontend]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]

SERVICE_COMMANDS: dict[str, tuple[list[str], Path]] = {
    "backend": (["python", "-m", "scripts.dev_run", "backend"], REPO_ROOT),
    "ingestion": (["python", "-m", "scripts.dev_run", "ingestion"], REPO_ROOT),
    "frontend": (["npm", "run", "dev"], REPO_ROOT / "frontend"),
}


def _run_steps(steps: Sequence[Sequence[str]], cwd: Path | None = None) -> int:
    for step in steps:
        display = " ".join(step)
        print(f"\n$ {display}")
        result = subprocess.run(step, cwd=cwd or REPO_ROOT)
        if result.returncode != 0:
            return result.returncode
    return 0


def command_tests(pytest_args: list[str]) -> int:
    """Run pytest with optional extra arguments."""
    cmd = ["pytest"]
    if pytest_args:
        cmd.extend(pytest_args)
    print(f"$ {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=REPO_ROOT)


def command_lint() -> int:
    """Run the standard lint/format suite."""
    steps: list[list[str]] = [
        ["black", "--check", "--line-length", "127", "."],
        ["isort", "--check-only", "--profile", "black", "."],
        ["flake8", ".", "--max-line-length", "127"],
        ["yamllint", ".github/workflows"],
    ]
    compose = REPO_ROOT / "docker-compose.yml"
    if compose.exists():
        steps.append(["yamllint", "docker-compose.yml"])
    return _run_steps(steps)


def command_services(names: list[str]) -> int:
    """Launch backend, ingestion, and/or frontend dev servers."""
    selected = names or ["backend", "ingestion", "frontend"]
    invalid = [name for name in selected if name not in SERVICE_COMMANDS]
    if invalid:
        print(f"Unknown services: {', '.join(invalid)}", file=sys.stderr)
        return 2

    procs: list[tuple[str, subprocess.Popen[bytes]]] = []
    try:
        for name in selected:
            cmd, cwd = SERVICE_COMMANDS[name]
            display = " ".join(cmd)
            print(f"Starting {name}: {display}")
            procs.append((name, subprocess.Popen(cmd, cwd=cwd)))

        print("Services running. Press Ctrl+C to stop all processes.")
        while True:
            exited = [name for name, proc in procs if proc.poll() is not None]
            if exited:
                for name in exited:
                    print(f"{name} exited.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        for name, proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for name, proc in procs:
            if proc.poll() is None:
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"Forcing {name} to stop...")
                    proc.kill()
        for name, proc in procs:
            code = proc.returncode
            if code:
                print(f"{name} exited with code {code}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Developer helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tests_parser = subparsers.add_parser("tests", help="Run pytest (pass-through args via --)")
    tests_parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Arguments after -- are passed to pytest")

    subparsers.add_parser("lint", help="Run lint/format checks")

    services_parser = subparsers.add_parser("services", help="Launch backend + ingestion + frontend dev servers")
    services_parser.add_argument(
        "--services",
        nargs="+",
        choices=sorted(SERVICE_COMMANDS.keys()),
        help="Subset of services to launch (default: backend ingestion frontend)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "tests":
        pytest_args = [arg for arg in args.pytest_args if arg != "--"]
        return command_tests(pytest_args)
    if args.command == "lint":
        return command_lint()
    if args.command == "services":
        return command_services(args.services or [])
    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
