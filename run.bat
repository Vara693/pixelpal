@echo off
REM Windows launcher for PixelPal.
REM Creates a local virtual environment on first run, then launches the app.

cd /d "%~dp0"

if not exist ".venv" (
    echo Setting up virtual environment ^(first run only^)...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul
    pip install -e .
) else (
    call .venv\Scripts\activate.bat
)

python -m pixelpal.main %*
