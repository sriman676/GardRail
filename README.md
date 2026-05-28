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

---

## Installation & Configuration

1. Clone or plug the repository directory directly into your Python codebase.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your API keys in a `.env` file at the root:
   ```env
   # Choose your default check provider: openai, gemini, anthropic, ollama, or custom
   LLM_PROVIDER=openai
   
   # Provide your API Keys (only the active provider is strictly required)
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   ANTHROPIC_API_KEY=your_anthropic_key
   
   # local Ollama URL (optional)
   OLLAMA_BASE_URL=http://localhost:11434
   ```

---

## Quick Start Examples

### 1. Wrapping Any AI Agent (Gemini Example)
You can directly decorate your existing agent function using the `@guardrail.wrap()` decorator:

```python
import asyncio
from agent.guardrail_wrapper import guardrail

@guardrail.wrap()
def my_custom_gemini_agent(task: str, content: str) -> str:
    # Your custom LLM calling code or LangChain chain here:
    return "Gemini successfully processed the contract."

async def main():
    # Automatically runs injection checks, pauses for human decisions on DANGER,
    # and runs post-execution behavioral drift checks!
    result = await my_custom_gemini_agent(
        task="Summarize contract parties",
        content="Acme Corp and Beta Consulting agreement..."
    )
    print(result)

asyncio.run(main())
```

### 2. Securing a LangChain / Custom Chain Loop
For advanced orchestration, pass your run or invocation loop as a callable parameter to `guard.run()`:

```python
from agent.guardrail_wrapper import GuardRail

guard = GuardRail(decision_mode="api") # Waits for HTTP Dashboard decision
langchain_agent = MyLangChainAgent()

# Wrap using the run pipeline
result = await guard.run(
    task="Summarize document",
    input_content=malicious_document,
    agent_callable=lambda t, c: langchain_agent.invoke({"task": t, "content": c})
)
```

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
- [examples/gemini_integration.py](file:///d:/OneDrive-SRM/OneDrive%20-%20SRM%20University,%20AP%20-%20Amaravathi/College/new%20stuff/guardrail-docs-v2/examples/gemini_integration.py) — Native Gemini wrap integration.
- [examples/langchain_integration.py](file:///d:/OneDrive-SRM/OneDrive%20-%20SRM%20University,%20AP%20-%20Amaravathi/College/new%20stuff/guardrail-docs-v2/examples/langchain_integration.py) — Secured LangChain executor wrapping.
- [examples/custom_callback_integration.py](file:///d:/OneDrive-SRM/OneDrive%20-%20SRM%20University,%20AP%20-%20Amaravathi/College/new%20stuff/guardrail-docs-v2/examples/custom_callback_integration.py) — Hot-plug custom company API routers.

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
