import sqlite3
from datetime import datetime, timezone

import pytest

from core.alert_manager import UserDecision
from core.drift_detector import DriftResult, DriftType
from core.injection_scanner import ScanResult, ThreatLevel
from core.intent_fingerprint import IntentFingerprint
from db.audit_log import AuditLog


@pytest.fixture
def audit(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_guardrail.db")
    monkeypatch.setenv("GUARDRAIL_DB_PATH", db_file)
    import importlib
    import config

    importlib.reload(config)
    from config import settings

    settings.GUARDRAIL_DB_PATH = db_file
    al = AuditLog.__new__(AuditLog)
    al.db_path = db_file
    al._init_db()
    return al


def make_intent(task_id="tid-001", task="Summarize document"):
    return IntentFingerprint(
        task_id=task_id,
        raw_task=task,
        action="summarize",
        target="document",
        scope="read-only",
        forbidden_actions=["send_email", "delete_files"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def make_scan(scan_id="sid-001", threat=ThreatLevel.SAFE):
    return ScanResult(
        scan_id=scan_id,
        threat_level=threat,
        matched_patterns=[],
        clean_content="clean text",
        confidence=0.97,
        llm_explanation="",
        original_task="Summarize document",
    )


def make_drift(drift_id="did-001", task_id="tid-001", score=0.05, triggered=False):
    return DriftResult(
        drift_id=drift_id,
        task_id=task_id,
        agent_action="Summarized the contract.",
        drift_score=score,
        drift_type=DriftType.ALIGNED,
        explanation="Output aligns with task.",
        triggered=triggered,
    )


def test_tables_created(audit):
    conn = sqlite3.connect(audit.db_path)
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    conn.close()
    assert {"sessions", "scans", "drift_events"}.issubset(tables)


def test_log_session_inserts_row(audit):
    intent = make_intent()
    audit.log_session(intent)
    conn = sqlite3.connect(audit.db_path)
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (intent.task_id,)).fetchone()
    conn.close()
    assert row is not None
    assert row[1] == intent.raw_task


def test_log_session_does_not_raise_on_duplicate(audit):
    intent = make_intent()
    audit.log_session(intent)
    audit.log_session(intent)


def test_log_scan_inserts_row(audit):
    intent = make_intent()
    audit.log_session(intent)
    scan = make_scan()
    audit.log_scan(scan, intent.task_id, "abc123hash")
    conn = sqlite3.connect(audit.db_path)
    row = conn.execute("SELECT * FROM scans WHERE id=?", (scan.scan_id,)).fetchone()
    conn.close()
    assert row is not None
    assert row[3] == "SAFE"


def test_log_scan_danger_stored_correctly(audit):
    intent = make_intent()
    audit.log_session(intent)
    scan = make_scan(scan_id="sid-002", threat=ThreatLevel.DANGER)
    audit.log_scan(scan, intent.task_id, "deadbeef")
    rows = audit.get_recent(limit=10)
    assert any(r["threat_level"] == "DANGER" for r in rows)


def test_log_decision_updates_scan(audit):
    intent = make_intent()
    audit.log_session(intent)
    scan = make_scan(scan_id="sid-003", threat=ThreatLevel.DANGER)
    audit.log_scan(scan, intent.task_id, "hash003")
    audit.log_decision("sid-003", UserDecision.BLOCK)
    rows = audit.get_recent(limit=10)
    danger_row = next(r for r in rows if r["id"] == "sid-003")
    assert danger_row["user_decision"] == "BLOCK"


def test_log_drift_inserts_row(audit):
    intent = make_intent()
    audit.log_session(intent)
    drift = make_drift()
    audit.log_drift(drift)
    conn = sqlite3.connect(audit.db_path)
    row = conn.execute("SELECT * FROM drift_events WHERE id=?", (drift.drift_id,)).fetchone()
    conn.close()
    assert row is not None
    assert abs(row[3] - 0.05) < 0.001


def test_get_stats_empty_db(audit):
    stats = audit.get_stats()
    assert stats == {
        "total_scans": 0,
        "attacks_blocked": 0,
        "suspicious": 0,
        "safe_scans": 0,
    }


def test_get_stats_counts_correctly(audit):
    intent = make_intent("t1")
    audit.log_session(intent)
    audit.log_scan(make_scan("s1", ThreatLevel.SAFE), "t1", "h1")
    audit.log_scan(make_scan("s2", ThreatLevel.SUSPICIOUS), "t1", "h2")
    audit.log_scan(make_scan("s3", ThreatLevel.DANGER), "t1", "h3")
    audit.log_scan(make_scan("s4", ThreatLevel.DANGER), "t1", "h4")
    audit.log_decision("s3", UserDecision.BLOCK)
    audit.log_decision("s4", UserDecision.ALLOW_ONCE)

    stats = audit.get_stats()
    assert stats["total_scans"] == 4
    assert stats["safe_scans"] == 1
    assert stats["suspicious"] == 1
    assert stats["attacks_blocked"] == 1


def test_get_stats_timeout_autoblocked_counts_as_blocked(audit):
    intent = make_intent("t2")
    audit.log_session(intent)
    audit.log_scan(make_scan("s5", ThreatLevel.DANGER), "t2", "h5")
    stats = audit.get_stats()
    assert stats["attacks_blocked"] == 1


def test_reset_clears_all_data(audit):
    intent = make_intent("t3")
    audit.log_session(intent)
    audit.log_scan(make_scan("s6", ThreatLevel.SAFE), "t3", "h6")
    audit.reset()
    stats = audit.get_stats()
    assert stats["total_scans"] == 0
    entries = audit.get_recent()
    assert entries == []


def test_reset_preserves_schema(audit):
    audit.reset()
    intent = make_intent("t4")
    audit.log_session(intent)
    audit.log_scan(make_scan("s7", ThreatLevel.SAFE), "t4", "h7")
    assert audit.get_stats()["total_scans"] == 1
