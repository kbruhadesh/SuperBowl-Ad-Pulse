@echo off
REM Start the SuperBowl Ad Pulse API (Windows)

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo Starting SuperBowl Ad Pulse API on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
