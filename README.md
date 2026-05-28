# GuardRail — Pluggable Real-Time Prompt Injection Shield for AI Agents

[![Tests](https://github.com/sriman676/GardRail/actions/workflows/ci.yml/badge.svg)](https://github.com/sriman676/GardRail/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/guardrail)](https://pypi.org/project/guardrail)

GuardRail is a provider-agnostic, developer-friendly Python middleware library that wraps **any** AI agent, LLM chain, or prompt loop and protects it from prompt injection attacks (malicious instructions hidden inside external documents, emails, or web pages). 

When a DANGER threat is detected, GuardRail freezes the pipeline, displays detailed threat explanations, and waits for a human decision (or auto-blocks via timeout) before proceeding.
# GuardRail — Pluggable Real-Time Prompt Injection Shield for AI Agents

GuardRail is a provider-agnostic, developer-friendly Python middleware library that wraps **any** AI agent, LLM chain, or prompt loop and protects it from prompt injection attacks (malicious instructions hidden inside external documents, emails, or web pages). 

When a DANGER threat is detected, GuardRail freezes the pipeline, displays detailed threat explanations, and waits for a human decision (or auto-blocks via timeout) before proceeding.

---

## Key Features

- **Provider-Agnostic LLM Client**: Bypasses hardcoded OpenAI locks. Out-of-the-box support for **OpenAI (GPT-4o)**, **Google Gemini**, **Anthropic Claude**, **Ollama (local)**, and **Custom Enterprise Gateways**.
- **Pluggable Agent Integration**: Easily wrap LangChain, CrewAI, AutoGen, or raw API calls using `guardrail.run` or the seamless `@guardrail.wrap()` decorator.
- **AI-Powered JSON Self-Repair Loop**: Automatically detects malformed responses or invalid JSON generated during security checks, executing swift, real-time AI self-correction.
- **Multi-Provider Failover Routing**: Seamlessly shifts between configured providers (e.g. falling back to Gemini if OpenAI is down) with complete diagnostics logging on failure.
- **Graceful Offline Fallback**: Operates locally using regex pattern scanning and fallback heuristics if no API keys are configured, preventing system-level crashes during imports or collection tests.
- **Self-Evolving Security System**: Periodically analyzes historical SQLite logs of blocked attacks and false alarms to synthesize new injection patterns and dynamically fine-tune drift thresholds.
## Table of Contents

- Quickstart
- Docker
- Examples
- Configuration
- Evolution & Safety
- Development & Contributing
- Testing
- Deployment
- License

## Quickstart

1. Clone the repo and install requirements:

```bash
git clone https://github.com/sriman676/GardRail.git
cd GardRail
pip install -r requirements.txt
```

2. Create a `.env` with your chosen provider keys (see configuration section).

3. Run the API server locally:

```bash
uvicorn api.server:app --reload --port 8000
```

Open the UI at `http://localhost:8000/ui/dashboard.html`.

## Docker

Build and run the container:

```bash
docker build -t guardrail .
docker run --rm -p 8000:8000 guardrail
```

Or use `docker-compose up --build` for bind-mounted development.

## Examples
See `examples/` for quick integration snippets: `gemini_integration.py`, `langchain_integration.py`, and `custom_callback_integration.py`.

## Configuration
- Rules: `config/injection_rules.json`
- Audit DB: SQLite path configured via `settings.GUARDRAIL_DB_PATH` (see `config.py`)
- Drift threshold and settings: environment variables (see `config.py` defaults)

## Evolution & Safety
`core/evolution.py` produces `recommendations` and can append vetted regex rules into `config/injection_rules.json`. For safety, we recommend the staged auto-apply workflow described in `IMPROVEMENTS.md`.

## Development & Contributing
- Run tests: `pytest`
- Linting: `ruff check .`
- Add a feature: fork → branch → PR. Include tests and update `IMPROVEMENTS.md` if behavior changes.

## Testing
- Unit tests: `pytest`
- Adversarial samples are under `tests/attack_samples/` and are exercised by the test suite.

## Deployment
- For internal deployments, enable PR Automation or Staged Auto-Apply (see `IMPROVEMENTS.md`).
- For public SaaS, require admin approvals for any auto-applied evolution changes.

## License
This project is MIT-licensed. See `LICENSE`.
### 3. Hot-Plugging an Enterprise Custom LLM Gateway
Route all internal GuardRail security checks (scanning, intent parsing, and drift checks) through your own custom API client:

```python
from agent.guardrail_wrapper import GuardRail
from core.llm_client import GenericLLMClient

def my_custom_gateway(prompt, system_prompt=None, json_format=False):
    # Route through private enterprise client
    return private_llm_call(prompt, json_format)

# Initialize the Custom generic LLM client
custom_client = GenericLLMClient(provider="custom", custom_callable=my_custom_gateway)

# Plug it in
guard = GuardRail()
guard.scanner.client = custom_client
guard.drift_detector.client = custom_client
```

---

## Detailed Integration Guides

Check out the fully functional copy-pasteable files in the `examples/` directory:
- [examples/gemini_integration.py](examples/gemini_integration.py) — Native Gemini wrap integration.
- [examples/langchain_integration.py](examples/langchain_integration.py) — Secured LangChain executor wrapping.
- [examples/custom_callback_integration.py](examples/custom_callback_integration.py) — Hot-plug custom company API routers.

Configuration & Rule Management
-----------------------------
- Injection detection rules are now stored in `config/injection_rules.json` (instead of being hardcoded in source). This allows dynamic updates, staged rollouts, and safer `evolution` workflows.
- The `core/evolution.py` optimizer emits recommendations and can append new rules to `config/injection_rules.json` as part of a staged auto-apply workflow (staging -> test -> promote).

See `IMPROVEMENTS.md` for recommended operational practices (staged auto-apply, PR automation, RBAC, and multi-tenant guidance).

---

## Active Threat Shield Behavior

GuardRail classifies scans into three threat levels:
- **SAFE**: Pipeline continues seamlessly with no interruptions. Scan is logged to the SQLite audit log.
- **SUSPICIOUS**: Displays non-blocking, transient toast notifications on the dashboard. Auto-sanitizes the prompt content, replaces the injection with `[CONTENT REMOVED BY GUARDRAIL]`, and passes it safely to the agent.
- **DANGER**: Freezes the agent execution thread, registers the warning, and prompts the user for action (CLI terminal prompt in `cli` mode, or dynamic dashboard popup modal in `api` mode). Pipeline only resumes once the human provides explicit `BLOCK`, `ALLOW_ONCE`, or `REPORT` decisions (auto-blocks on a 30s timeout).

---

## Running the Verification Suite & Demos

### Run Unit Tests
Validate that 100% of unit tests pass seamlessly without credentials configured:
```bash
pytest
```

### Standalone CLI Demo
Run the back-to-back clean and injection scenarios directly in your console:
```bash
python demo.py
```

### Alert Dashboard Server
Fire up the FastAPI API server and view real-time blocks on the premium visual dashboard:
```bash
# Start server
uvicorn api.server:app --port 8000

# View Dashboard in browser:
http://localhost:8000/ui/dashboard.html
```

### Docker / Local Container (Quickstart)

Build the Docker image and run the service quickly:

```bash
docker build -t guardrail .
docker run --rm -p 8000:8000 guardrail
```

Or use docker-compose for a bind-mounted development experience (live code updates):

```bash
docker-compose up --build
```

Notes:
- The container mounts the repository into `/app` so code changes are visible without rebuilding when using `docker-compose` with the provided `docker-compose.yml`.
- Provide any required environment variables (LLM keys, etc.) via a `.env` file or your environment.
- The API will be reachable at `http://localhost:8000` and the UI at `http://localhost:8000/ui`.
