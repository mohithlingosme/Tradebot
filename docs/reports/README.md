# Automated Project Report

Use ``scripts/generate_project_report.py`` to build a Markdown summary of the
project's open tasks and testing signal.

## Usage

```bash
# Generate docs/reports/project_status.md using checkbox tasks across the repo
python scripts/generate_project_report.py

# Write to a custom path
python scripts/generate_project_report.py --output /tmp/project_status.md

# Run tests and embed the output
python scripts/generate_project_report.py --run-tests --tests-command "pytest -q"
```

## Output

The script counts completed versus remaining checkbox tasks, groups them by
source file and section headings, and optionally appends the captured test run
output inside a collapsible block. Reports include a generation timestamp to aid
release tracking.
