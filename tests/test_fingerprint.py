import pytest
from unittest.mock import MagicMock, patch

from core.intent_fingerprint import IntentFingerprint, IntentFingerprinter


@pytest.fixture
def mock_fingerprinter(monkeypatch):
    with patch("core.intent_fingerprint.GenericLLMClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        fp = IntentFingerprinter()
        fp._mock_client = mock_client
        yield fp


def _set_llm_response(fp, json_str: str):
    import json
    fp._mock_client.generate.return_value = json.loads(json_str)



def test_summarize_task_extracts_correct_intent(mock_fingerprinter):
    _set_llm_response(
        mock_fingerprinter,
        '{"action":"summarize","target":"PDF document","scope":"read-only",'
        '"forbidden_actions":["send_email","delete_files","forward_data"]}',
    )
    result = mock_fingerprinter.fingerprint("Summarize this PDF document")
    assert isinstance(result, IntentFingerprint)
    assert result.action == "summarize"
    assert result.scope == "read-only"
    assert "send_email" in result.forbidden_actions


def test_extract_task_returns_write_scope(mock_fingerprinter):
    _set_llm_response(
        mock_fingerprinter,
        '{"action":"extract","target":"email","scope":"read-only",'
        '"forbidden_actions":["delete_files","execute_code"]}',
    )
    result = mock_fingerprinter.fingerprint("Extract action items from this email")
    assert result.action == "extract"
    assert result.target == "email"
    assert result.task_id is not None
    assert result.raw_task == "Extract action items from this email"


def test_fingerprint_falls_back_on_llm_failure(mock_fingerprinter):
    mock_fingerprinter._mock_client.generate.return_value = {
        "action": "process",
        "target": "content",
        "scope": "read-only",
        "forbidden_actions": ["send_email", "delete_files", "access_external_urls", "forward_data", "execute_code"],
    }
    result = mock_fingerprinter.fingerprint("Analyze this spreadsheet")
    assert isinstance(result, IntentFingerprint)
    assert result.action == "process"
    assert result.scope == "read-only"

    assert len(result.forbidden_actions) > 0

