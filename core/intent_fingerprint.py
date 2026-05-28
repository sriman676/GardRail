import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from core.llm_client import GenericLLMClient

logger = logging.getLogger("guardrail.fingerprint")


@dataclass
class IntentFingerprint:
    task_id: str
    raw_task: str
    action: str
    target: str
    scope: str
    forbidden_actions: List[str]
    timestamp: str


INTENT_EXTRACTION_PROMPT = """You are an intent parser for an AI security system.

Given a user task, extract a structured intent object.
Return ONLY valid JSON with these exact keys:
- "action": string (primary verb, e.g. "summarize", "analyze", "extract", "translate")
- "target": string (what the action applies to, e.g. "PDF document", "email", "webpage")
- "scope": string (one of exactly: "read-only", "write", "execute", "mixed")
- "forbidden_actions": array of strings (actions NOT implied by this task)

For forbidden_actions, choose from this list only:
send_email, delete_files, access_external_urls, create_files,
modify_system, forward_data, share_content, execute_code, download_files, upload_files

User task: {task}

Respond with JSON only. No explanation. No markdown. No code fences."""

DEFAULT_FORBIDDEN = [
    "send_email",
    "delete_files",
    "access_external_urls",
    "forward_data",
    "execute_code",
]


class IntentFingerprinter:
    def __init__(self):
        self.client = GenericLLMClient()

    def fingerprint(self, task: str) -> IntentFingerprint:
        task_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        data = self._extract(task)
        return IntentFingerprint(
            task_id=task_id,
            raw_task=task,
            action=data.get("action", "process"),
            target=data.get("target", "content"),
            scope=data.get("scope", "read-only"),
            forbidden_actions=data.get("forbidden_actions", DEFAULT_FORBIDDEN),
            timestamp=timestamp,
        )

    def _extract(self, task: str) -> dict:
        fallback = {
            "action": "process",
            "target": "content",
            "scope": "read-only",
            "forbidden_actions": DEFAULT_FORBIDDEN,
        }
        data = self.client.generate(
            prompt=INTENT_EXTRACTION_PROMPT.format(task=task),
            json_format=True,
            temperature=0,
            max_tokens=500,
            fallback_default=fallback
        )
        logger.info(
            "Intent fingerprinted: action=%s scope=%s",
            data.get("action"),
            data.get("scope"),
        )
        return data

