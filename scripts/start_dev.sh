#!/bin/bash
# Start GardRail development server on macOS/Linux

set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Run: source scripts/setup_local.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "Run: cp .env.example .env (if available) or create manually"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 Starting GardRail Development Server"
echo "======================================="
echo ""
echo "📍 API Server:    http://localhost:8000"
echo "📚 Swagger UI:    http://localhost:8000/docs"
echo "📖 ReDoc:         http://localhost:8000/redoc"
echo "🎨 Dashboard:     http://localhost:8000/ui/dashboard.html"
echo "📊 Metrics:       http://localhost:8000/metrics"
echo "❤️  Health Check:   http://localhost:8000/health/detailed"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server with auto-reload
python -m uvicorn api.server:app --reload --host 127.0.0.1 --port 8000
