#!/usr/bin/env python3
"""Generate a unified status report for the Finbot project."""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"node_modules", ".git", "__pycache__"}
MAX_TASKS_PER_FILE = 5


def run_command(command: Sequence[str]) -> str:
    try:
        return (
            subprocess.check_output(command, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
            .strip()
        )
    except subprocess.CalledProcessError:
        return ""


def find_todo_files() -> list[Path]:
    todos = []
    for path in ROOT.rglob("*TODO*.md"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        todos.append(path)
    return sorted(todos)


def parse_tasks(path: Path) -> list[dict]:
    tasks = []
    current_section = path.stem
    pattern = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.+)")
    header_pattern = re.compile(r"^\s{0,3}(#{1,6})\s*(.+)")
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        header_match = header_pattern.match(raw_line)
        if header_match:
            current_section = header_match.group(2).strip()
        task_match = pattern.match(raw_line)
        if not task_match:
            continue
        state, text = task_match.groups()
        tasks.append(
            {
                "text": text.strip(),
                "done": state.lower() == "x",
                "context": current_section,
                "line": lineno,
                "file": path,
            }
        )
    return tasks


def summarize_tasks(tasks: Iterable[dict]) -> tuple[int, int, int]:
    total = sum(1 for _ in tasks)
    done = sum(1 for task in tasks if task["done"])
    return total, done, total - done


def gather_testing_commands() -> list[str]:
    commands = []
    pytest_ini = ROOT / "pytest.ini"
    if pytest_ini.exists():
        commands.append("pytest")
    package_json = ROOT / "package.json"
    if package_json.exists():
        data = json.loads(package_json.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        for name, script in scripts.items():
            if "test" in name.lower() or "lint" in name.lower():
                commands.append(f"npm run {name}")
    frontend_pkg = ROOT / "frontend" / "package.json"
    if frontend_pkg.exists():
        data = json.loads(frontend_pkg.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        for name, script in scripts.items():
            if "test" in name.lower() or "lint" in name.lower():
                commands.append(f"cd frontend && npm run {name}")
    return sorted(set(commands))


def format_git_summary() -> list[str]:
    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    commit = run_command(["git", "log", "-1", "--pretty=format:%h %ci %s"])
    status = run_command(["git", "status", "-sb"])
    status_lines = status.splitlines()[1:] if status else []
    dirty = len([line for line in status_lines if line and not line.startswith("??")])
    untracked = len([line for line in status_lines if line.startswith("??")])
    return [
        f"- Branch: `{branch or 'unknown'}`",
        f"- Latest commit: `{commit or 'not available'}`",
        f"- Working tree: {'clean' if dirty == 0 else 'has changes'}",
        f"- Untracked entries: {untracked}",
    ]


def build_report(output: Path | None) -> str:
    todos = find_todo_files()
    all_tasks = []
    tasks_by_file = {}
    for path in todos:
        file_tasks = parse_tasks(path)
        if not file_tasks:
            continue
        tasks_by_file[path] = file_tasks
        all_tasks.extend(file_tasks)

    total, done, remaining = summarize_tasks(all_tasks)
    testing_cmds = gather_testing_commands()

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    report_lines = [
        "# Finbot Project Health Report",
        "",
        f"_Generated on {timestamp} UTC_",
        "",
        "## Project Status",
        *format_git_summary(),
        "- TODO coverage: "
        f"{len(tasks_by_file)} tracked files, {total} tasks ({remaining} remaining, {done} done)",
        "",
        "## Outstanding Tasks",
    ]

    if not tasks_by_file:
        report_lines.append("All tracked TODO files are empty or missing task markers.")
    else:
        for path, file_tasks in sorted(
            tasks_by_file.items(),
            key=lambda pair: (
                sum(1 for t in pair[1] if not t["done"]),
                len(pair[1]),
            ),
            reverse=True,
        ):
            outstanding = [task for task in file_tasks if not task["done"]]
            if not outstanding:
                continue
            report_lines.append(f"### {path.relative_to(ROOT)}")
            report_lines.append(
                f"- Remaining: {len(outstanding)} / {len(file_tasks)} tasks (context snapshot follows)"
            )
            shown = outstanding[:MAX_TASKS_PER_FILE]
            for task in shown:
                report_lines.append(
                    f"  - {task['text']} _(section: {task['context']}, line {task['line']})_"
                )
            if len(outstanding) > MAX_TASKS_PER_FILE:
                report_lines.append(
                    f"  - ... and {len(outstanding) - MAX_TASKS_PER_FILE} more outstanding items"
                )
            report_lines.append("")

    report_lines.extend(
        [
            "## Testing & Validation",
            "- Recommended commands for the next pass:",
        ]
    )
    if testing_cmds:
        report_lines.extend(f"  - `{cmd}`" for cmd in testing_cmds)
    else:
        report_lines.append("  - No automated test command was detected; please document one.")
    report_lines.append("")
    report_lines.append("## Notes")
    report_lines.append(
        "- Run this generator regularly (see docs/project-report.md) and keep TODO files updated."
    )

    text = "\n".join(report_lines)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Markdown status report for Finbot.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=ROOT / "reports" / "project-status.md",
        help="File to write the report to (also printed to stdout).",
    )
    args = parser.parse_args()
    report = build_report(args.output)
    print(report)


if __name__ == "__main__":
    main()
