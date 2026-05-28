#!/bin/bash
# Start GardRail production server on macOS/Linux

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
    echo "❌ .env file not found"
    echo "Create .env with required API keys"
    exit 1
fi

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ] && [ -z "$GEMINI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    if ! grep -q "OPENAI_API_KEY\|GEMINI_API_KEY\|ANTHROPIC_API_KEY" .env; then
        echo "❌ No LLM provider API key configured in .env"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting GardRail Production Server"
echo "======================================"
echo ""
echo "⚙️  Using workers: 4"
echo "🔒 Host: 0.0.0.0"
echo "🔧 Port: 8000"
echo ""
echo "📍 API Server:    http://localhost:8000"
echo "📚 Swagger UI:    http://localhost:8000/docs"
echo "📊 Metrics:       http://localhost:8000/metrics"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start production server with gunicorn
pip install -q gunicorn

gunicorn api.server:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
