"""Generate an automatic project status report.

The report summarizes Markdown checkbox tasks across the repository, highlights
remaining work, and optionally embeds the latest test run output. By default it
stores the report under ``docs/reports/project_status.md``.

Usage examples:

```
python scripts/generate_project_report.py
python scripts/generate_project_report.py --output /tmp/report.md
python scripts/generate_project_report.py --run-tests --tests-command "pytest -q"
```
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import re
import subprocess
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

EXCLUDED_DIR_NAMES = {".git", "node_modules", "dist", "build", "__pycache__"}
TASK_PATTERN = re.compile(r"^- \[(?P<state>[ xX])\] (?P<description>.+)$")
HEADING_PATTERN = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+)$")


@dataclasses.dataclass
class Task:
    description: str
    completed: bool
    section: str | None


@dataclasses.dataclass
class TaskFile:
    path: Path
    tasks: List[Task]

    @property
    def completed(self) -> int:
        return sum(1 for task in self.tasks if task.completed)

    @property
    def remaining(self) -> int:
        return sum(1 for task in self.tasks if not task.completed)

    @property
    def completion_ratio(self) -> float:
        if not self.tasks:
            return 0.0
        return self.completed / len(self.tasks)


@dataclasses.dataclass
class TestRun:
    command: str
    success: bool
    output: str


def find_markdown_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.md"):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        yield path


def parse_tasks(content: str) -> List[Task]:
    tasks: List[Task] = []
    section_stack: List[str] = []
    for line in content.splitlines():
        heading_match = HEADING_PATTERN.match(line.strip())
        if heading_match:
            level = len(heading_match.group("level"))
            title = heading_match.group("title").strip()
            section_stack = section_stack[: level - 1]
            section_stack.append(title)
            continue

        task_match = TASK_PATTERN.match(line.strip())
        if task_match:
            completed = task_match.group("state").lower() == "x"
            description = task_match.group("description").strip()
            section = " > ".join(section_stack) if section_stack else None
            tasks.append(Task(description=description, completed=completed, section=section))
    return tasks


def collect_task_files(paths: Iterable[Path]) -> List[TaskFile]:
    task_files: List[TaskFile] = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        tasks = parse_tasks(content)
        if tasks:
            task_files.append(TaskFile(path=path, tasks=tasks))
    return task_files


def run_tests(command: str) -> TestRun:
    result = subprocess.run(
        command,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return TestRun(command=command, success=result.returncode == 0, output=output.strip())


def format_task_summary(task_files: Sequence[TaskFile]) -> list[str]:
    total_tasks = sum(len(file.tasks) for file in task_files)
    completed_tasks = sum(file.completed for file in task_files)
    remaining_tasks = total_tasks - completed_tasks
    completion_percent = (completed_tasks / total_tasks * 100) if total_tasks else 0.0

    lines = ["## Project Status", ""]
    lines.append(f"- Total tasks: {total_tasks}")
    lines.append(f"- Completed tasks: {completed_tasks}")
    lines.append(f"- Remaining tasks: {remaining_tasks}")
    lines.append(f"- Completion: {completion_percent:.1f}%")
    return lines


def format_file_breakdown(task_files: Sequence[TaskFile], *, max_tasks_per_section: int = 8) -> list[str]:
    lines = ["## Remaining Tasks by File", ""]
    for task_file in sorted(task_files, key=lambda file: str(file.path)):
        if not task_file.tasks:
            continue
        total = len(task_file.tasks)
        remaining = task_file.remaining
        completion = (task_file.completed / total * 100) if total else 0.0
        lines.append(f"### {task_file.path}")
        lines.append(f"- Remaining: {remaining}/{total} ({completion:.1f}% complete)")

        pending_tasks: dict[str | None, list[str]] = {}
        for task in task_file.tasks:
            if task.completed:
                continue
            pending_tasks.setdefault(task.section, []).append(task.description)

        for section, tasks in pending_tasks.items():
            if section:
                lines.append(f"- **{section}**")
            else:
                lines.append("- **General**")
            for description in tasks[:max_tasks_per_section]:
                lines.append(f"  - [ ] {description}")
        lines.append("")
    return lines


def format_test_section(test_run: TestRun | None) -> list[str]:
    if not test_run:
        return [
            "## Testing",
            "",
            "- Tests not executed for this report. Run with `--run-tests` to include results.",
            "",
        ]

    status = "passed" if test_run.success else "failed"
    lines = ["## Testing", ""]
    lines.append(f"- Command: `{test_run.command}`")
    lines.append(f"- Status: **{status.upper()}**")
    lines.append("")
    if test_run.output:
        lines.append("<details><summary>Test output</summary>")
        lines.append("")
        lines.append("```")
        lines.extend(test_run.output.splitlines())
        lines.append("```")
        lines.append("</details>")
        lines.append("")
    return lines


def build_report(task_files: Sequence[TaskFile], test_run: TestRun | None) -> str:
    timestamp = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = ["# Automated Project Report", ""]
    lines.append(f"Generated: {timestamp}")
    lines.append("")
    lines.extend(format_task_summary(task_files))
    lines.append("")
    lines.extend(format_file_breakdown(task_files))
    lines.extend(format_test_section(test_run))
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a project status report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/reports/project_status.md"),
        help="Destination path for the generated report.",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run the test command and embed the output in the report.",
    )
    parser.add_argument(
        "--tests-command",
        default="pytest -q --disable-warnings --maxfail=1",
        help="Shell command to run when --run-tests is enabled.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown_files = list(find_markdown_files(Path(".")))
    task_files = collect_task_files(markdown_files)
    test_run = run_tests(args.tests_command) if args.run_tests else None

    report = build_report(task_files, test_run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")

    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
