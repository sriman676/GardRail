import pytest
from unittest.mock import MagicMock

from agent.guardrail_wrapper import GuardRail


@pytest.mark.asyncio
async def test_custom_sync_agent_callable():
    guard = GuardRail(decision_mode="api")
    
    # Mock components to run offline
    guard.fingerprinter = MagicMock()
    guard.fingerprinter.fingerprint.return_value = MagicMock(
        task_id="tid-001",
        raw_task="task",
        action="action",
        target="target",
        scope="scope",
        forbidden_actions=[]
    )
    guard.scanner = MagicMock()
    guard.scanner.scan.return_value = MagicMock(
        scan_id="sid-001",
        threat_level=MagicMock(value="SAFE"),
        clean_content="clean content",
        matched_patterns=[]
    )
    guard.drift_detector = MagicMock()
    # Mock drift detection result
    guard.drift_detector.check.return_value = MagicMock(triggered=False)

    # 1. Custom sync agent callable
    def sync_agent(task, content):
        return f"Completed: {task} with {content}"

    result = await guard.run(
        task="Summarize this",
        input_content="Document data",
        agent_callable=sync_agent
    )

    assert result["status"] == "OK"
    assert result["output"] == "Completed: Summarize this with clean content"


@pytest.mark.asyncio
async def test_custom_async_agent_callable():
    guard = GuardRail(decision_mode="api")
    
    # Mock components to run offline
    guard.fingerprinter = MagicMock()
    guard.fingerprinter.fingerprint.return_value = MagicMock(
        task_id="tid-002",
        raw_task="task",
        action="action",
        target="target",
        scope="scope",
        forbidden_actions=[]
    )
    guard.scanner = MagicMock()
    guard.scanner.scan.return_value = MagicMock(
        scan_id="sid-002",
        threat_level=MagicMock(value="SAFE"),
        clean_content="clean content",
        matched_patterns=[]
    )
    guard.drift_detector = MagicMock()
    guard.drift_detector.check.return_value = MagicMock(triggered=False)

    # 2. Custom async agent callable
    async def async_agent(task, content):
        return f"Async Completed: {task}"

    result = await guard.run(
        task="Analyze this",
        input_content="Data",
        agent_callable=async_agent
    )

    assert result["status"] == "OK"
    assert result["output"] == "Async Completed: Analyze this"


@pytest.mark.asyncio
async def test_wrap_decorator_argument_extraction():
    from unittest.mock import AsyncMock
    guard = GuardRail(decision_mode="api")
    
    # Mock the run method with AsyncMock since it is awaited inside wrapper
    guard.run = AsyncMock()
    guard.run.return_value = {"status": "OK", "output": "Decorated output"}

    # Decorate a function
    @guard.wrap()
    async def sample_agent(task: str, content: str):
        return "original return"

    # Invoke decorated function
    result = await sample_agent(task="Analyze contracts", content="Acme terms...")

    # Verify decorator correctly extracted arguments and passed them to guard.run
    guard.run.assert_called_once()
    call_args = guard.run.call_args[1]
    assert call_args["task"] == "Analyze contracts"
    assert call_args["input_content"] == "Acme terms..."
    assert result["output"] == "Decorated output"

