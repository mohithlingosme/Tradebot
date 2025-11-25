# Automated Project Reporting

This project-level report pulls together the current git status, outstanding TODOs, and available test commands so you can understand where Finbot stands without digging into spreadsheets or multiple markdown files.

## Running locally

1. Ensure you are on the correct branch and working tree (the script will report your branch and dirty/untracked files).
2. Run the generator from the repository root:

```bash
python scripts/project_report.py
```

The default output file is `reports/project-status.md`, but you can override it with `--output <path>` if you want to stage the report somewhere else before sharing it.

## Continuous reporting

A dedicated GitHub workflow (`.github/workflows/project-report.yml`) runs this script on demand (via `workflow_dispatch`) and on a daily schedule. The artifact `project-status-report` is uploaded so you can download the latest snapshot from the Actions UI without cloning the repo.

## Reading the report

- **Project Status** lists git metadata plus a summary of how many TODO files are being tracked.
- **Outstanding Tasks** surfaces up to five unchecked tasks per TODO file, annotated with the last header they appeared under. The most active files appear first.
- **Testing & Validation** echoes the test/lint commands detected in `package.json` and `pytest.ini`.
- **Notes** reminds contributors to keep TODO files accurate and rerun the generator before major status updates.

Use the report as a lightweight daily stand-up document, or paste relevant sections into your update emails or Slack threads.

## Customization ideas

1. Add new TODO files to the `*TODO*.md` glob if you want them included.
2. Extend `scripts/project_report.py` to surface metrics from other systems (bugs, release status, etc.).
3. Consume the Markdown artifact in other reports (e.g., convert to HTML via CI) if you need prettier output.
