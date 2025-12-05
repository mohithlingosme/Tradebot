"""Tests for the automated project report generator."""

from scripts.generate_project_report import Task, TaskFile, build_report, parse_tasks
from tests.utils.paths import repo_path


def test_parse_tasks_with_sections():
    content = """
# Phase 1
## Backend
- [ ] Implement authentication
- [x] Add health endpoint
"""
    tasks = parse_tasks(content)

    assert len(tasks) == 2
    assert tasks[0].description == "Implement authentication"
    assert not tasks[0].completed
    assert tasks[0].section == "Phase 1 > Backend"
    assert tasks[1].completed


def test_build_report_includes_summary_and_pending_items():
    task_file = TaskFile(
        path=repo_path("TODO.md"),
        tasks=[Task(description="Task A", completed=False, section="Phase A"), Task(description="Task B", completed=True, section=None)],
    )

    report = build_report([task_file], test_run=None)

    assert "Total tasks: 2" in report
    assert "Remaining tasks: 1" in report
    assert "TODO.md" in report
    assert "[ ] Task A" in report
