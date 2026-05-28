#!/bin/bash
# Setup script for macOS/Linux

set -e

echo "🔧 Setting up GardRail locally..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MIN_VERSION="3.11"

if [ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$MIN_VERSION" ]; then
    echo "✓ Python $PYTHON_VERSION (required >= $MIN_VERSION)"
else
    echo "✗ Python $PYTHON_VERSION - required >= $MIN_VERSION"
    exit 1
fi

# Create virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install -q --upgrade pip setuptools wheel

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# LLM Provider Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Optional: Other providers
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=...

# Optional: Admin API Keys
ADMIN_API_KEYS=your-admin-key

# Optional: JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-change-in-production
JWT_EXPIRATION_HOURS=24

# Server Configuration
GUARDRAIL_HOST=127.0.0.1
GUARDRAIL_PORT=8000
LOG_LEVEL=INFO
EOF
    echo "  ⚠️  Update .env with your API keys"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Update .env with your API keys"
echo "  3. Run server: python -m uvicorn api.server:app --reload"
echo "  4. Visit: http://localhost:8000/docs"
echo ""
echo "💡 Or use the Makefile:"
echo "  make install     # Install dependencies"
echo "  make run-dev     # Start dev server"
echo "  make test        # Run tests"
echo "  make help        # See all commands"
