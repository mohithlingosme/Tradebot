@echo off
echo [Finbot] Installing core dependencies (API, DB, auth, logging)...
pip install -r "%~dp0..\\requirements-core.txt"
if %errorlevel% neq 0 (
    echo [Finbot] Installation failed. Make sure your virtualenv is active.
    exit /b %errorlevel%
)
echo [Finbot] Core dependencies installed.
