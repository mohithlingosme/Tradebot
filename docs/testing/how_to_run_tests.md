# How to run tests locally

This document shows local commands to run tests and e2e scenarios.

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dev dependencies:

```powershell
pip install -r requirements-dev.txt
```

3. Run unit tests:

```powershell
pytest tests/unit -q
```

4. Run integration tests:

```powershell
pytest tests/integration -q
```

5. Run e2e tests:

```powershell
pytest tests/e2e -q
```

Notes:
- Ensure `.env` or environment variables are set correctly for integrations that use database paths or log file locations.
- CI should run `pip install -r requirements-dev.txt` and then run `pytest -q` as part of the pipeline.
