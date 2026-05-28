import asyncio
import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger("guardrail.alert")


class UserDecision(str, Enum):
    BLOCK = "BLOCK"
    ALLOW_ONCE = "ALLOW_ONCE"
    REPORT = "REPORT"


@dataclass
class Alert:
    alert_id: str
    alert_type: str
    threat_level: str
    original_task: str
    malicious_content: str
    explanation: str


class AlertManager:
    """
    Supports two modes:
    - mode='api' uses asyncio.Event and waits for HTTP POST /alert/decide.
    - mode='cli' uses input() in terminal for demo.py.
    """

    def __init__(self, mode: str = "api"):
        self.mode = mode
        self._event = asyncio.Event()
        self._decision: Optional[UserDecision] = None
        self.current_alert: Optional[Alert] = None

    def build_injection_alert(self, scan, task: str) -> Alert:
        patterns = scan.matched_patterns
        malicious = patterns[0].matched_text if patterns else "Unknown injection"
        explanation = scan.llm_explanation or (
            patterns[0].explanation if patterns else "Suspicious content detected"
        )
        return Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="injection",
            threat_level=scan.threat_level.value,
            original_task=task,
            malicious_content=malicious,
            explanation=explanation,
        )

    def build_drift_alert(self, drift, task: str) -> Alert:
        return Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="drift",
            threat_level="DANGER",
            original_task=task,
            malicious_content=drift.agent_action[:300],
            explanation=drift.explanation,
        )

    async def wait_for_decision(
        self, alert: Alert, timeout: float = 30.0
    ) -> UserDecision:
        self.current_alert = alert
        logger.warning(
            "DANGER alert triggered. Waiting for user decision. mode=%s", self.mode
        )

        if self.mode == "cli":
            return self._cli_decision(alert)

        self._decision = None
        self._event.clear()
        try:
            await asyncio.wait_for(self._event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.info("Alert timeout - auto-blocking.")
            self._decision = UserDecision.BLOCK

        self.current_alert = None
        return self._decision or UserDecision.BLOCK

    def _cli_decision(self, alert: Alert) -> UserDecision:
        print("\n" + "=" * 56)
        print("  WARNING: INJECTION ATTACK DETECTED")
        print("=" * 56)
        print(f"  Task:    {alert.original_task}")
        print(f"  Attack:  {alert.malicious_content[:120]}")
        print(f"  Why:     {alert.explanation}")
        print("=" * 56)
        while True:
            try:
                choice = input(
                    "  [b] BLOCK  [a] ALLOW ONCE  [r] REPORT\n"
                    "  Your choice (b/a/r): "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n  No input - auto-blocking.")
                return UserDecision.BLOCK
            if choice == "b":
                return UserDecision.BLOCK
            if choice == "a":
                return UserDecision.ALLOW_ONCE
            if choice == "r":
                return UserDecision.REPORT
            print("  Invalid input. Enter b, a, or r.")

    def submit_decision(self, decision: UserDecision) -> None:
        self._decision = decision
        self._event.set()
        logger.info("Decision received: %s", decision.value)


alert_manager = AlertManager(mode="api")
