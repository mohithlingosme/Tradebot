# Environment Setup (Python 3.11.9)

Finbot now targets Python 3.11.9. Trading/analytics libraries (numpy, pandas, pandas-ta, scikit-learn) are pinned to 3.11-compatible versions. Follow these steps on Windows/macOS/Linux.

## 1) Install Python 3.11.9
- Download from https://www.python.org/downloads/release/python-3119/ (Windows: check “Add Python to PATH”).

## 2) Create and activate a virtual environment
```bash
. # Windows
py -3.11 -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

## 3) Upgrade pip and install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
The dependency stack is split across layered requirement files; `requirements.txt` includes them all. `pandas-ta` is pinned to a PyPI-available version range compatible with Python 3.11.

## 4) Verify imports
```bash
python - <<'PY'
import sys
import numpy, pandas, pandas_ta
print("Python", sys.version)
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("pandas_ta", pandas_ta.__version__)
PY
```

## 5) Troubleshooting
- If a system build tool error occurs (e.g., TA-Lib), stay on `pandas-ta` only or install TA-Lib via WSL2/Docker. TA-Lib is optional in `requirements-indicators.txt`.
-- Ensure you are using Python 3.11.9; mismatched interpreters can cause “requires a different python version” errors.

## 6) Clean reinstall (fresh setup)
```bash
deactivate  # if active
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install --upgrade pip
pip install -r requirements.txt
```
