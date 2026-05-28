@echo off
REM Start GardRail production server on Windows

setlocal enabledelayedexpansion

REM Check if virtual environment exists
if not exist "venv\" (
    echo ❌ Virtual environment not found
    echo Run: scripts\setup_local.bat
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo ❌ .env file not found
    echo Create .env with required API keys
    exit /b 1
)

echo.
echo 🚀 Starting GardRail Production Server
echo ======================================
echo.
echo ⚙️  Using workers: 2
echo 🔒 Host: 0.0.0.0
echo 🔧 Port: 8000
echo.
echo 📍 API Server:    http://localhost:8000
echo 📚 Swagger UI:    http://localhost:8000/docs
echo 📊 Metrics:       http://localhost:8000/metrics
echo.
echo Press Ctrl+C to stop the server
echo.

REM Install gunicorn
pip install -q gunicorn

REM Start production server
gunicorn api.server:app ^
    --workers 2 ^
    --worker-class uvicorn.workers.UvicornWorker ^
    --bind 0.0.0.0:8000 ^
    --access-logfile - ^
    --error-logfile - ^
    --log-level info
