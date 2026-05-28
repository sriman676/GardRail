# GardRail Quick Start Guide

Get up and running with GardRail in 5 minutes!

## Choose Your Setup

### 🚀 Fastest: Automated Setup (Recommended)

**Linux/macOS:**
```bash
source scripts/setup_local.sh
source scripts/start_dev.sh
```

**Windows:**
```cmd
scripts\setup_local.bat
scripts\start_dev.bat
```

Visit: **http://localhost:8000/docs**

---

### 📦 Using Make (All Platforms)

```bash
make install      # First time only
make run-dev      # Start server
make test         # Run tests
```

---

### 🔧 Manual Setup

**1. Create environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate.bat (Windows)
pip install -r requirements.txt
```

**2. Configure API key:**
```bash
cp .env.template .env
# Edit .env and add your OPENAI_API_KEY or other LLM provider key
```

**3. Start server:**
```bash
python -m uvicorn api.server:app --reload --port 8000
```

**4. Open Swagger UI:**
Visit: **http://localhost:8000/docs**

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/run` | Main: scan + drift + execute |
| `/scan` | Scan only |
| `/alert/decide` | Human decision on threats |
| `/health/detailed` | Component health |
| `/metrics` | Prometheus metrics |
| `/docs` | Swagger UI |

---

## Common Commands

```bash
# Development
make run-dev          # Auto-reload server
make test             # Run tests
make test-watch       # Watch mode

# Code quality
make lint             # Check code style
make format           # Auto-format code
make type-check       # Type checking

# Production
make run              # Production server (4 workers)
make install-prod     # Production dependencies only

# Utilities
make clean            # Remove cache
make demo             # Run demo scenarios
```

---

## Environment Variables

Minimal `.env`:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
ADMIN_API_KEYS=your-admin-key
```

Full `.env` reference: See `.env.template`

---

## Troubleshooting

### Import Error: "No module named 'uvicorn'"
```bash
source scripts/setup_local.sh  # or: scripts\setup_local.bat on Windows
```

### Port 8000 already in use?
```bash
# Try different port
python -m uvicorn api.server:app --port 8001
```

### LLM API Key errors?
1. Update `.env` with valid API key
2. Verify LLM_PROVIDER matches (openai, gemini, etc.)
3. Check `/health/detailed` endpoint for diagnostics

### Tests fail?
```bash
make clean             # Remove cache
python -m pytest tests/ -v
```

---

## Next Steps

1. ✅ Read the main [README.md](README.md) for full documentation
2. 📚 Explore API with [Swagger UI](http://localhost:8000/docs)
3. 🧪 Run demo: `make demo` or `python demo.py`
4. 📊 Check metrics: http://localhost:8000/metrics
5. 🚀 Deploy with Docker: `docker-compose up`

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/ui/dashboard.html
- **Logs**: Check JSON structured logs in terminal output
- **Health**: http://localhost:8000/health/detailed
- **Issues**: [GitHub Issues](https://github.com/sriman676/GardRail/issues)
