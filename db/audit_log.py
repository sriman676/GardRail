import dataclasses
import json
import logging
import os
import sqlite3
from typing import Any, Optional

from config import settings

logger = logging.getLogger("guardrail.db")


class AuditLog:
    def __init__(self):
        self.db_path = settings.GUARDRAIL_DB_PATH
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        parent = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(parent, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, raw_task TEXT NOT NULL, intent_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'active');
                CREATE TABLE IF NOT EXISTS scans (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, input_hash TEXT NOT NULL,
                    threat_level TEXT NOT NULL, scan_result_json TEXT, user_decision TEXT, rule_version TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id));
                CREATE TABLE IF NOT EXISTS drift_events (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, agent_action TEXT NOT NULL,
                    drift_score REAL NOT NULL, drift_type TEXT, explanation TEXT,
                    triggered INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id));
                CREATE INDEX IF NOT EXISTS idx_scans_session ON scans(session_id);
                CREATE INDEX IF NOT EXISTS idx_scans_threat ON scans(threat_level);
                CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at);
                CREATE INDEX IF NOT EXISTS idx_drift_session ON drift_events(session_id);
                CREATE INDEX IF NOT EXISTS idx_drift_triggered ON drift_events(triggered);
                CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
                """
            )

    def log_session(self, intent) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO sessions (id, raw_task, intent_json) VALUES (?,?,?)",
                    (
                        intent.task_id,
                        intent.raw_task,
                        json.dumps(dataclasses.asdict(intent), default=str),
                    ),
                )
        except Exception as e:
            logger.error("log_session failed: %s", e)

    def log_scan(self, scan: Any, session_id: str, input_hash: str) -> None:
        try:
            with self._connect() as conn:
                # Prepare values with explicit coercion to avoid None type issues
                scan_id = str(getattr(scan, "scan_id", ""))
                _tl = getattr(scan, "threat_level", "")
                # If it's an enum with .value, persist the value (e.g., 'SAFE')
                try:
                    threat_level = _tl.value if hasattr(_tl, "value") else str(_tl)
                except Exception:
                    threat_level = str(_tl)
                scan_json = json.dumps(dataclasses.asdict(scan), default=str)
                rule_version = getattr(scan, "rule_version", "") or ""

                conn.execute(
                    "INSERT INTO scans (id, session_id, input_hash, threat_level, scan_result_json, rule_version) VALUES (?,?,?,?,?,?)",
                    (
                        scan_id,
                        session_id,
                        input_hash,
                        threat_level,
                        scan_json,
                        rule_version,
                    ),
                )
        except Exception as e:
            logger.error("log_scan failed: %s", e)

    def log_drift(self, drift) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO drift_events (id, session_id, agent_action, drift_score, drift_type, explanation, triggered) VALUES (?,?,?,?,?,?,?)",
                    (
                        drift.drift_id,
                        drift.task_id,
                        drift.agent_action,
                        drift.drift_score,
                        drift.drift_type.value,
                        drift.explanation,
                        int(drift.triggered),
                    ),
                )
        except Exception as e:
            logger.error("log_drift failed: %s", e)

    def log_decision(self, scan_id: str, decision) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE scans SET user_decision=? WHERE id=?",
                    (decision.value, scan_id),
                )
        except Exception as e:
            logger.error("log_decision failed: %s", e)

    def get_recent(self, limit: int = 50, threat_level: Optional[str] = None) -> list:
        try:
            with self._connect() as conn:
                if threat_level:
                    rows = conn.execute(
                        "SELECT * FROM scans WHERE threat_level=? ORDER BY created_at DESC LIMIT ?",
                        (threat_level, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM scans ORDER BY created_at DESC LIMIT ?",
                        (limit,),
                    ).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error("get_recent failed: %s", e)
            return []

    def get_stats(self) -> dict:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS total_scans,
                        SUM(CASE WHEN threat_level='DANGER'
                                  AND (user_decision IS NULL OR user_decision != 'ALLOW_ONCE')
                                 THEN 1 ELSE 0 END) AS attacks_blocked,
                        SUM(CASE WHEN threat_level='SUSPICIOUS' THEN 1 ELSE 0 END) AS suspicious,
                        SUM(CASE WHEN threat_level='SAFE' THEN 1 ELSE 0 END) AS safe_scans
                    FROM scans
                    """
                ).fetchone()
                return {
                    "total_scans": row["total_scans"] or 0,
                    "attacks_blocked": row["attacks_blocked"] or 0,
                    "suspicious": row["suspicious"] or 0,
                    "safe_scans": row["safe_scans"] or 0,
                }
        except Exception as e:
            logger.error("get_stats failed: %s", e)
            return {
                "total_scans": 0,
                "attacks_blocked": 0,
                "suspicious": 0,
                "safe_scans": 0,
            }

    def reset(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(
                    """
                    DELETE FROM drift_events;
                    DELETE FROM scans;
                    DELETE FROM sessions;
                    """
                )
            logger.info("Audit log reset - all data cleared.")
        except Exception as e:
            logger.error("reset failed: %s", e)
            raise
