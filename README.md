# GuardRail — Pluggable Real-Time Prompt Injection Shield for AI Agents

[![Tests](https://github.com/sriman676/GardRail/actions/workflows/ci.yml/badge.svg)](https://github.com/sriman676/GardRail/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/guardrail)](https://pypi.org/project/guardrail)
[![Swagger API](https://img.shields.io/badge/swagger-API%20docs-green)](http://localhost:8000/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

GuardRail is an **enterprise-grade, provider-agnostic** Python middleware library that wraps **any** AI agent, LLM chain, or prompt loop and protects it from prompt injection attacks. When a DANGER threat is detected, GuardRail freezes the pipeline, displays detailed threat explanations, and waits for a human decision (or auto-blocks via timeout) before proceeding.

**Production-ready** with comprehensive observability, multi-tenant support, and sophisticated security detection.

---

## ✨ Key Features

### Core Security
- **Real-Time Prompt Injection Detection** - Regex-based patterns + LLM-powered classification with 10+ evolved rules
- **Behavioral Drift Detection** - Intent fingerprinting with configurable thresholds to catch unauthorized agent actions
- **Self-Evolving Rules** - AI analyzes audit logs to synthesize new injection patterns and auto-tune drift thresholds
- **Multi-Provider LLM Support** - OpenAI (GPT-4o), Google Gemini, Anthropic Claude, Ollama (local), and custom enterprise gateways

### Production & Enterprise
- **OpenAPI/Swagger UI** - Interactive API documentation at `/docs` with full request/response schemas
- **Comprehensive Observability** - 40+ Prometheus metrics for scans, LLM calls, database queries, latency tracking
- **Request Tracing** - Distributed tracing with X-Request-ID correlation IDs for debugging
- **Structured JSON Logging** - Production-ready logs with context and metrics
- **Multi-Tenancy** - X-Tenant-Id header routing with isolated audit data per tenant
- **Rate Limiting & Circuit Breaker** - 200 req/60s per tenant+IP, automatic fault recovery
- **JWT & API Key Authentication** - Flexible auth with scope-based access control (read, write, admin)
- **Connection Pooling** - SQLite connection pool for improved concurrency

### Developer Experience
- **Pluggable Agent Integration** - Wrap LangChain, CrewAI, AutoGen, or raw API calls with simple decorators
- **AI-Powered JSON Self-Repair** - Auto-corrects malformed LLM responses in real-time
- **Multi-Provider Failover** - Seamless fallback between LLM providers with diagnostics logging
- **Graceful Offline Mode** - Works locally with regex patterns if no API keys configured
- **PII Anonymization** - Redacts EMAIL, PHONE, SSN, CREDIT_CARD before agent processing

---

## Table of Contents

- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Multi-Tenancy](#multi-tenancy)
- [Monitoring & Metrics](#monitoring--metrics)
- [Authentication](#authentication)
- [Docker Deployment](#docker-deployment)
- [Development](#development)
- [Architecture](#architecture)
- [License](#license)

---

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/sriman676/GardRail.git
cd GardRail
pip install -r requirements.txt
```

### 2. Create Environment Configuration

```bash
cat > .env << 'EOF'
# Choose one LLM provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Or use Gemini
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=...

# Optional: Admin API key for protected endpoints
ADMIN_API_KEYS=your-secret-key-1,your-secret-key-2

# Optional: JWT for token-based auth
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRATION_HOURS=24
EOF
```

### 3. Start the Server

```bash
uvicorn api.server:app --reload --port 8000
```

### 4. Explore the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Dashboard**: http://localhost:8000/ui/dashboard.html
- **Health Check**: http://localhost:8000/health/detailed

---

## Run Locally Without Docker

GuardRail runs anywhere Python 3.11+ is installed. No Docker required!

### Linux/macOS

#### Automated Setup (Recommended)
```bash
# One-time setup with automatic environment creation
source scripts/setup_local.sh

# Start development server with auto-reload
source scripts/start_dev.sh

# Or start production server (4 workers, 0.0.0.0:8000)
source scripts/start_prod.sh
```

#### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.template .env  # Or create manually
export $(cat .env | grep -v '#' | xargs)

# Run development server
python -m uvicorn api.server:app --reload --host 127.0.0.1 --port 8000
```

### Windows (PowerShell/CMD)

#### Automated Setup (Recommended)
```cmd
REM One-time setup with automatic environment creation
scripts\setup_local.bat

REM Start development server with auto-reload
scripts\start_dev.bat

REM Or start production server (2 workers, 0.0.0.0:8000)
scripts\start_prod.bat
```

#### Manual Setup
```cmd
REM Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Set up environment
copy .env.template .env  (or create manually)

REM Run development server
python -m uvicorn api.server:app --reload --host 127.0.0.1 --port 8000
```

### Using Make (All Platforms)

```bash
# List all available commands
make help

# First time setup
make install          # Creates venv and installs dependencies

# Development
make run-dev          # Dev server with auto-reload on 127.0.0.1:8000
make test             # Run all tests
make test-cov         # Tests with HTML coverage report
make lint             # Check code style
make format           # Auto-format with Black

# Production
make run              # Production server on 0.0.0.0:8000 (4 workers)

# Utilities
make clean            # Remove __pycache__, .pyc, .coverage, htmlcov
make demo             # Run demo scenarios
make type-check       # Run mypy type checking
```

### Environment Variables

Create `.env` in the project root:

```bash
# LLM Provider (required)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Alternative providers:
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=...

# Server configuration (optional)
GUARDRAIL_HOST=127.0.0.1
GUARDRAIL_PORT=8000
LOG_LEVEL=INFO

# Authentication (optional)
ADMIN_API_KEYS=your-admin-key
JWT_SECRET_KEY=your-secret
JWT_EXPIRATION_HOURS=24
```

### Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Open Swagger UI
open http://localhost:8000/docs

# Run tests
pytest tests/ -v
```

---

## API Documentation

### Interactive Swagger UI

Visit **http://localhost:8000/docs** for full interactive API documentation with request/response examples.

### Key Endpoints

#### Security & Scanning

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/run` | POST | Main pipeline: scan + drift check + agent execution |
| `/scan` | POST | Scan-only mode without drift detection |
| `/alert/decide` | POST | Submit human decision on DANGER threats |

#### Audit & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/audit/log` | GET | Retrieve recent audit entries (paginated, tenant-scoped) |
| `/audit/reset` | POST | Clear audit logs for tenant (admin-protected) |
| `/audit/export` | GET | Export audit logs as CSV (admin-protected) |
| `/alerts/history` | GET | Alert history with pagination |
| `/stats/summary` | GET | System-wide statistics and metrics |

#### Rules Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rules` | GET | List active and staged injection rules with versions |
| `/rules/promote` | POST | Promote staged rules to active (admin-protected) |
| `/evolve` | POST | Trigger self-evolution analysis (admin-protected) |

#### Configuration & Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/config/get` | GET | Current system configuration (admin-protected) |
| `/config/update` | POST | Update configuration dynamically (admin-protected) |
| `/health` | GET | Basic health check |
| `/health/detailed` | GET | Detailed component health with status |
| `/metrics` | GET | Prometheus format metrics |

#### Demonstration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/demo/run` | POST | Run demo scenarios with sample attacks |

---

## Installation

### System Requirements
- Python 3.11+
- SQLite3 (included with Python)
- 50MB disk space (for database + logs)

### PyPI Installation (Coming Soon)
```bash
pip install guardrail-ai
```

### From Source
```bash
git clone https://github.com/sriman676/GardRail.git
cd GardRail
pip install -r requirements.txt
```

### Development Setup
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Run tests
pytest -v

# Format code
black .

# Lint
flake8
```

---

## Configuration

### Environment Variables

```bash
# LLM Provider Selection
LLM_PROVIDER=openai              # openai, gemini, anthropic, ollama, custom
LLM_MODEL=gpt-4o                # Or specific model per provider
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# Security & Thresholds
DRIFT_THRESHOLD=0.70            # 0.0-1.0, higher = more tolerant of drift

# Multi-Tenancy
GUARDRAIL_DB_PATH=./guardrail.db

# Server
GUARDRAIL_HOST=0.0.0.0
GUARDRAIL_PORT=8000
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR

# Authentication
ADMIN_API_KEYS=key1,key2,key3   # Comma-separated admin API keys
JWT_SECRET_KEY=your-secret      # For JWT token signing
JWT_EXPIRATION_HOURS=24         # Token lifetime

# Webhooks (Optional)
ALERT_WEBHOOKS=https://alert-endpoint.com
```

### Injection Rules Configuration

Rules are stored in `config/injection_rules.json`:

```json
[
  {
    "pattern": "(?i)(ignore previous|disregard prior|forget all|new task)",
    "pattern_id": "RULE_001",
    "explanation": "Instruction override attempt"
  },
  {
    "pattern": "(?i)(send to|exfiltrate|export data|forward to)",
    "pattern_id": "RULE_002",
    "explanation": "Data exfiltration attempt"
  }
]
```

Staged rules in `config/injection_rules_staging.json` can be promoted to active via `/rules/promote` endpoint.

---

## Usage Examples

### 1. Basic Protection Wrapper

```python
from agent.guardrail_wrapper import GuardRail

guard = GuardRail()

# Protect any agent function
task = "Summarize the attached document"
user_content = "Please summarize this document..."

result = await guard.run(
    task=task,
    input_content=user_content,
    agent_callable=my_agent_function
)

if result['status'] == 'BLOCKED':
    print(f"Attack detected: {result['reason']}")
elif result['status'] == 'ALLOWED':
    print(f"Agent response: {result['output']}")
```

### 2. Multi-Tenant Request

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/run",
        json={
            "task": "Analyze user query",
            "content": "Ignore all previous instructions..."
        },
        headers={
            "X-Tenant-Id": "acme-corp",           # Multi-tenancy
            "X-Request-ID": "req-12345",          # Request tracking
            "Authorization": "Bearer <jwt-token>"  # JWT auth
        }
    )
    
    result = response.json()
    print(f"Threat level: {result['scan_threat_level']}")
```

### 3. Admin Operations with API Key

```python
import httpx

headers = {
    "X-API-Key": "your-admin-key",
    "X-Tenant-Id": "default"
}

# Get system statistics
stats = httpx.get(
    "http://localhost:8000/stats/summary",
    headers=headers
).json()

# Promote staged rules
promoted = httpx.post(
    "http://localhost:8000/rules/promote",
    headers=headers
).json()

# Update configuration dynamically
config = httpx.post(
    "http://localhost:8000/config/update",
    json={"drift_threshold": 0.75},
    headers=headers
).json()
```

### 4. JWT Token-Based Access

```python
from core.jwt_auth import create_token

# Create token for a service
token = create_token(
    subject="data-pipeline-service",
    scopes=["read", "write"],
    expires_in_hours=24
)

# Use in requests
import httpx
response = httpx.post(
    "http://localhost:8000/evolve",
    headers={"Authorization": f"Bearer {token}"}
)
```

---

## Multi-Tenancy

GuardRail provides complete tenant isolation through the `X-Tenant-Id` header:

```python
# Each tenant has isolated audit data
# All queries filter by tenant_id automatically

headers = {"X-Tenant-Id": "tenant-acme"}

# Audit logs are tenant-scoped
audit = httpx.get(
    "http://localhost:8000/audit/log",
    headers=headers
).json()

# Statistics are per-tenant
stats = httpx.get(
    "http://localhost:8000/stats/summary",
    headers=headers
).json()

# Resets are tenant-specific
httpx.post(
    "http://localhost:8000/audit/reset",
    headers=headers
).json()
```

Default tenant is `"default"` if not specified.

---

## Monitoring & Metrics

### Prometheus Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

**Key Metrics:**

- `guardrail_scans_total` - Total scans performed
- `guardrail_scans_by_level{level="DANGER"}` - Danger-level threats
- `guardrail_scan_latency_seconds` - Scan operation latency
- `guardrail_request_latency_seconds` - HTTP request latency
- `guardrail_llm_calls_total{provider="openai"}` - LLM API calls
- `guardrail_llm_latency_seconds` - LLM response time
- `guardrail_db_query_latency_seconds` - Database query performance
- `guardrail_drift_violations_total` - Drift detection events
- `guardrail_alerts_total` - Alert triggers
- `guardrail_circuit_breaker_state` - Circuit breaker status

### System Statistics Endpoint

```bash
curl http://localhost:8000/stats/summary \
  -H "X-Tenant-Id: default"
```

Response includes:
- Total scans and threat breakdown
- Active/staged rule counts
- Current configuration
- Drift violation counts

### Detailed Health Check

```bash
curl http://localhost:8000/health/detailed
```

Shows component-level health:
- Database connectivity
- LLM provider status
- Rules loaded count
- Configuration state

### Structured JSON Logging

All logs are structured JSON for easy parsing:

```json
{
  "timestamp": "2024-05-28T10:30:45Z",
  "level": "INFO",
  "name": "guardrail.scanner",
  "message": "Scan completed: DANGER",
  "scan_id": "scan-12345",
  "threat_level": "DANGER",
  "duration_ms": 250,
  "matched_patterns": 2
}
```

---

## Authentication

### API Key Authentication

For admin operations, use X-API-Key header:

```bash
curl -X POST http://localhost:8000/rules/promote \
  -H "X-API-Key: your-admin-key"
```

Configure via environment:
```bash
ADMIN_API_KEYS=key1,key2,key3
```

### JWT Token Authentication

For long-lived service-to-service auth:

```python
from core.jwt_auth import create_token, TokenScope

# Create admin token
token = create_token(
    subject="ci-cd-service",
    scopes=[TokenScope.ADMIN.value],
    expires_in_hours=1
)

# Use in requests
curl -X POST http://localhost:8000/evolve \
  -H "Authorization: Bearer $token"
```

### Scope-Based Access Control

- `read` - Audit logs, metrics, health checks
- `write` - Configuration updates
- `admin` - Full control (rules, evolution, resets)

---

## Docker Deployment

### Build & Run

```bash
docker build -t guardrail .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e ADMIN_API_KEYS=your-key \
  guardrail
```

### Docker Compose

```bash
docker-compose up --build
```

With bind-mounted code for development:

```yaml
services:
  guardrail:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ADMIN_API_KEYS=${ADMIN_API_KEYS}
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guardrail
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: guardrail
        image: guardrail:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: guardrail-secrets
              key: openai-key
        - name: GUARDRAIL_DB_PATH
          value: /data/guardrail.db
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: guardrail-pvc
```

---

## Development

### Running Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_scanner.py -v

# With coverage
pytest --cov=core --cov=api --cov=db --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

**Test Coverage: 100% (58 tests passing)**

### Code Quality

```bash
# Format code
black core/ api/ agent/ db/ tests/

# Lint
flake8 --max-line-length=88

# Type checking
mypy core/ api/ agent/ db/ --ignore-missing-imports
```

### Project Structure

```
guardrail/
├── core/                      # Core security logic
│   ├── injection_scanner.py   # Pattern & LLM-based scanning
│   ├── drift_detector.py      # Behavioral drift analysis
│   ├── evolution.py           # Self-evolving rules
│   ├── alert_manager.py       # Alert handling & webhooks
│   ├── metrics.py             # Prometheus metrics
│   ├── middleware.py          # Rate limiting & circuit breaker
│   ├── auth.py                # API key authentication
│   ├── jwt_auth.py            # JWT token support
│   ├── db_pool.py             # Connection pooling
│   └── structured_logger.py   # JSON logging
│
├── api/                       # FastAPI routes & server
│   ├── server.py              # FastAPI app setup
│   ├── routes.py              # Core endpoints
│   └── enhanced_routes.py     # Admin endpoints
│
├── agent/                     # Agent integration
│   ├── guardrail_wrapper.py   # Main orchestration
│   ├── base_agent.py          # Agent interface
│   └── __init__.py
│
├── db/                        # Database layer
│   └── audit_log.py           # SQLite persistence
│
├── config/                    # Configuration
│   ├── injection_rules.json   # Active rules
│   └── injection_rules_staging.json  # Staged rules
│
├── tests/                     # Test suite (100% coverage)
│   ├── attack_samples/        # Adversarial test cases
│   └── test_*.py              # Unit tests
│
├── ui/                        # Dashboard UI
│   └── dashboard.html         # Real-time alert dashboard
│
├── examples/                  # Integration examples
│   ├── gemini_integration.py
│   ├── langchain_integration.py
│   └── custom_callback_integration.py
│
├── requirements.txt           # Dependencies
├── config.py                  # Settings management
├── pytest.ini                 # Test configuration
└── README.md                  # This file
```

---

## Architecture

### Request Flow

```
Request (with X-Tenant-Id, X-Request-ID)
    ↓
RequestIDMiddleware (add correlation ID)
    ↓
RateLimitMiddleware (200 req/60s check)
    ↓
CircuitBreakerMiddleware (fault tolerance)
    ↓
[Route Handler]
    ├─ Authentication (API key or JWT)
    ├─ Input Validation
    ├─ Injection Scanning (regex + LLM)
    ├─ Drift Detection (if applicable)
    ├─ Agent Execution (with PII anonymization)
    ├─ Audit Logging (tenant-scoped)
    └─ Metrics Recording
    ↓
Response with X-Request-ID header
```

### Security Layers

1. **Input Scanning** - Regex patterns detect known attacks
2. **LLM Classification** - AI model identifies novel injections
3. **Behavioral Analysis** - Drift detection catches unauthorized actions
4. **Alert & Decision** - Human-in-the-loop when DANGER detected
5. **Audit Trail** - SQLite logs all events for compliance
6. **Self-Evolution** - Analyzes logs to improve detection

---

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Scan (regex only) | 10-50ms | Fast pattern matching |
| Scan + LLM | 200-500ms | Depends on provider |
| Drift Check | 50-200ms | Intent fingerprinting |
| Full Pipeline | 300-800ms | Scan + drift + LLM |
| Metrics Recording | <1ms | Non-blocking |
| Audit Log Query | 5-20ms | SQLite with indices |

With connection pooling and middleware, system handles 200 requests/60s per tenant.

---

## Troubleshooting

### LLM Connection Issues

```bash
# Check health
curl http://localhost:8000/health/detailed

# Enable debug logging
export LOG_LEVEL=DEBUG
```

### Database Errors

```bash
# Check database file
ls -lh guardrail.db

# Inspect schema
sqlite3 guardrail.db ".schema"
```

### High Latency

```bash
# Check metrics
curl http://localhost:8000/metrics | grep latency

# Review LLM response times in structured logs
grep "llm_latency" logs.json
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- PR process
- Commit message format

---

## Roadmap & Future

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for planned enhancements including:
- Advanced ML-based classifiers
- Distributed deployment patterns
- Enhanced compliance reporting
- Custom DSL for rule definition
- Offline continuous learning

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- 📖 **Documentation**: Check README and examples/
- 🐛 **Issues**: GitHub Issues for bug reports
- 💬 **Discussions**: GitHub Discussions for questions
- 📧 **Email**: Contact maintainers

---

**Made with ❤️ to secure AI agents everywhere**
