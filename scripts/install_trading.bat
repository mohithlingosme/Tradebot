@echo off
echo [Finbot] Installing trading stack (includes core + data providers/analytics)...
pip install -r "%~dp0..\\requirements-trading.txt"
if %errorlevel% neq 0 (
    echo [Finbot] Trading stack installation failed. Check that your virtualenv is active.
    exit /b %errorlevel%
)
echo [Finbot] Trading stack installed (core + trading layers).
