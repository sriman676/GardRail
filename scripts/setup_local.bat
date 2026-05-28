@echo off
REM Setup script for Windows

echo.
echo 🔧 Setting up GardRail locally...
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python not found. Please install Python 3.11+
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION%

REM Create virtual environment
if exist "venv\" (
    echo ✓ Virtual environment exists
) else (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install -q --upgrade pip setuptools wheel

REM Install dependencies
echo 📦 Installing dependencies...
pip install -q -r requirements.txt

REM Create .env if not exists
if not exist ".env" (
    echo 📝 Creating .env template...
    (
        echo # LLM Provider Configuration
        echo LLM_PROVIDER=openai
        echo OPENAI_API_KEY=sk-your-key-here
        echo OPENAI_MODEL=gpt-4o
        echo.
        echo # Optional: Other providers
        echo # LLM_PROVIDER=gemini
        echo # GEMINI_API_KEY=...
        echo.
        echo # Optional: Admin API Keys
        echo ADMIN_API_KEYS=your-admin-key
        echo.
        echo # Optional: JWT Configuration
        echo JWT_SECRET_KEY=your-jwt-secret-change-in-production
        echo JWT_EXPIRATION_HOURS=24
        echo.
        echo # Server Configuration
        echo GUARDRAIL_HOST=127.0.0.1
        echo GUARDRAIL_PORT=8000
        echo LOG_LEVEL=INFO
    ) > .env
    echo   ⚠️  Update .env with your API keys
)

echo.
echo ✨ Setup complete!
echo.
echo 📖 Next steps:
echo   1. Activate environment: venv\Scripts\activate.bat
echo   2. Update .env with your API keys
echo   3. Run server: python -m uvicorn api.server:app --reload
echo   4. Visit: http://localhost:8000/docs
echo.
