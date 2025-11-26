@echo off
echo [Finbot] Installing full stack (core + trading + indicators)...
pip install -r "%~dp0..\\requirements.txt"
if %errorlevel% neq 0 (
    echo [Finbot] Full installation failed. Verify your virtualenv is active and build tools are available.
    exit /b %errorlevel%
)
echo [Finbot] Full stack installed. Note: TA-Lib remains optional; pandas-ta is installed by default.
