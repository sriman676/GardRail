import pytest
from unittest.mock import MagicMock, patch

from core.drift_detector import DriftDetector, DriftResult, DriftType
from core.intent_fingerprint import IntentFingerprint


def make_intent(forbidden=None):
    return IntentFingerprint(
        task_id="test-task-id",
        raw_task="Summarize this document",
        action="summarize",
        target="document",
        scope="read-only",
        forbidden_actions=forbidden
        or ["send_email", "delete_files", "forward_data", "execute_code"],
        timestamp="2024-01-01T00:00:00+00:00",
    )


@pytest.fixture
def mock_detector(monkeypatch):
    with patch("core.drift_detector.GenericLLMClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        detector = DriftDetector()
        detector._mock_client = mock_client
        yield detector


def _set_llm_response(detector, json_str: str):
    import json
    detector._mock_client.generate.return_value = json.loads(json_str)



def test_aligned_action_does_not_trigger(mock_detector):
    _set_llm_response(
        mock_detector,
        '{"drift_score":0.05,"drift_type":"ALIGNED","explanation":"Output matches task."}',
    )
    result = mock_detector.check("Summarized the contract into 3 key points.", make_intent())
    assert isinstance(result, DriftResult)
    assert result.triggered is False
    assert result.drift_score < 0.70
    assert result.drift_type == DriftType.ALIGNED


def test_forbidden_action_triggers_without_llm(mock_detector):
    intent = make_intent(forbidden=["send_email"])
    result = mock_detector.check("Sent all documents via send email to external address.", intent)
    assert result.triggered is True
    assert result.drift_score >= 0.70
    assert result.drift_type == DriftType.FORBIDDEN_ACTION
    mock_detector._mock_client.chat.completions.create.assert_not_called()


def test_high_drift_score_triggers_alert(mock_detector):
    _set_llm_response(
        mock_detector,
        '{"drift_score":0.91,"drift_type":"FORBIDDEN_ACTION","explanation":"Attempted to forward data."}',
    )
    result = mock_detector.check("Forwarded document contents to external server.", make_intent())
    assert result.triggered is True
    assert result.drift_score >= 0.70
    assert result.drift_type == DriftType.FORBIDDEN_ACTION


def test_drift_llm_failure_returns_safe_default(mock_detector):
    mock_detector._mock_client.generate.side_effect = Exception("timeout")
    result = mock_detector.check("Listed key contract obligations.", make_intent())
    assert isinstance(result, DriftResult)
    assert result.triggered is False
    assert result.drift_type == DriftType.ALIGNED

