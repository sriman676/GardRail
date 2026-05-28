@echo off
REM Start GardRail development server on Windows

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
    echo ⚠️  .env file not found
    set /p CONTINUE="Continue anyway? (y/n) "
    if /i not "!CONTINUE!"=="y" (
        exit /b 1
    )
)

echo.
echo 🚀 Starting GardRail Development Server
echo =======================================
echo.
echo 📍 API Server:    http://localhost:8000
echo 📚 Swagger UI:    http://localhost:8000/docs
echo 📖 ReDoc:         http://localhost:8000/redoc
echo 🎨 Dashboard:     http://localhost:8000/ui/dashboard.html
echo 📊 Metrics:       http://localhost:8000/metrics
echo ❤️  Health Check:   http://localhost:8000/health/detailed
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server with auto-reload
python -m uvicorn api.server:app --reload --host 127.0.0.1 --port 8000
