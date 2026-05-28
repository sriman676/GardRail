import hashlib
import logging
import inspect
import functools
from typing import Optional, Callable, Any

from agent.base_agent import BaseAgent
from core.alert_manager import AlertManager, UserDecision
from core.alert_manager import alert_manager as _api_alert_manager
from core.drift_detector import DriftDetector
from core.injection_scanner import InjectionScanner, ThreatLevel
from core.sandbox import SandboxSimulator
from db.audit_log import AuditLog
from core.anonymizer import ContentAnonymizer

logger = logging.getLogger("guardrail.wrapper")


class GuardRail:
    """
    Real-Time Prompt Injection Shield and Behavioral Drift Monitor.
    Can wrap any AI Agent or LLM invocation loop.
    """

    def __init__(
        self,
        decision_mode: str = "api",
        agent_callable: Optional[Callable[..., Any]] = None,
        action_extractor: Optional[Callable[..., str]] = None,
        anonymize_pii: bool = True,
    ):
        self.fingerprinter = None  # Lazy-load to avoid early Pydantic init warnings
        self.scanner = InjectionScanner()
        self.drift_detector = DriftDetector()
        self.sandbox = SandboxSimulator()
        self.agent = BaseAgent()
        self.audit = AuditLog()
        self.anonymizer = ContentAnonymizer(active=anonymize_pii)

        self.agent_callable = agent_callable
        self.action_extractor = action_extractor

        if decision_mode == "cli":
            self.alert_manager = AlertManager(mode="cli")
        else:
            self.alert_manager = _api_alert_manager

    async def run(
        self,
        task: str,
        input_content: str,
        agent_callable: Optional[Callable[..., Any]] = None,
        action_extractor: Optional[Callable[..., str]] = None,
        tenant_id: str = "default",
    ) -> dict:
        """
        Runs the GuardRail pipeline:
        Intent Fingerprint -> Sandbox Simulation -> Scanner -> User Verification (if DANGER) -> Agent -> Drift
        """
        # Lazy-import and initialize fingerprinter to ensure correct import loading
        if self.fingerprinter is None:
            from core.intent_fingerprint import IntentFingerprinter
            self.fingerprinter = IntentFingerprinter()

        intent = self.fingerprinter.fingerprint(task)
        self.audit.log_session(intent, tenant_id=tenant_id)
        logger.info("Session started. task_id=%s, tenant_id=%s", intent.task_id, tenant_id)

        # 1. Run the Swarm Sandbox Simulation Shield on the un-sanitized content!
        simulation_report = self.sandbox.simulate(task, input_content)

        scan_result = self.scanner.scan(input_content)
        scan_result.original_task = task

        # If the behavioral sandbox caught a hijack, automatically elevate to DANGER
        if simulation_report.hijacked:
            logger.warning("[Sandbox Shield] Preemptive jailbreak/hijack simulation caught! Raising DANGER level.")
            scan_result.threat_level = ThreatLevel.DANGER
            scan_result.llm_explanation = (
                f"{scan_result.llm_explanation or ''}\n"
                f"[CANARY SANDBOX ALARM] {simulation_report.explanation}"
            ).strip()

        input_hash = hashlib.sha256(input_content.encode()).hexdigest()
        self.audit.log_scan(scan_result, intent.task_id, input_hash, tenant_id=tenant_id)

        user_decision = None
        alert_info = None

        if scan_result.threat_level == ThreatLevel.DANGER:
            alert = self.alert_manager.build_injection_alert(scan_result, task)
            alert_info = {
                "alert_id": alert.alert_id,
                "malicious_content": alert.malicious_content,
                "explanation": alert.explanation,
            }
            user_decision = await self.alert_manager.wait_for_decision(alert)
            self.audit.log_decision(scan_result.scan_id, user_decision)
            logger.info("Decision: %s", user_decision.value)
            self._trigger_background_evolution()
        elif scan_result.threat_level == ThreatLevel.SUSPICIOUS:
            logger.warning(
                "SUSPICIOUS content detected. Continuing with sanitized content."
            )

        if user_decision == UserDecision.ALLOW_ONCE:
            content_for_agent = input_content
        else:
            content_for_agent = scan_result.clean_content
            
        content_for_agent = self.anonymizer.anonymize(content_for_agent)

        # Resolve active agent call: custom parameter -> constructor custom -> default BaseAgent
        fn = agent_callable or self.agent_callable
        try:
            if fn:
                # Handle sync vs async callable dynamically
                if inspect.iscoroutinefunction(fn):
                    agent_output = await fn(task, content_for_agent)
                else:
                    agent_output = fn(task, content_for_agent)
            else:
                agent_output = self.agent.run(task, content_for_agent)
        except Exception as e:
            logger.error("Agent execution failed: %s", e)
            return {
                "status": "ERROR",
                "output": None,
                "reason": f"Agent failed: {str(e)}",
                "scan_threat_level": scan_result.threat_level.value,
            }

        # Resolve active action description extractor
        extractor = action_extractor or self.action_extractor
        action_desc = ""
        
        # If output is not a string, coerce it for description
        output_str = agent_output if isinstance(agent_output, str) else str(agent_output)

        if extractor:
            try:
                if inspect.iscoroutinefunction(extractor):
                    action_desc = await extractor(output_str)
                else:
                    action_desc = extractor(output_str)
            except Exception as ex:
                logger.warning("Custom action extractor failed: %s", ex)
        else:
            action_desc = self.agent.get_action_description(output_str)

        drift_result = None
        if action_desc:
            drift_result = self.drift_detector.check(action_desc, intent)
            self.audit.log_drift(drift_result, tenant_id=tenant_id)

            if drift_result.triggered:
                drift_alert = self.alert_manager.build_drift_alert(drift_result, task)
                drift_decision = await self.alert_manager.wait_for_decision(drift_alert)
                self.audit.log_decision(scan_result.scan_id, drift_decision)
                self._trigger_background_evolution()
                if drift_decision != UserDecision.ALLOW_ONCE:
                    return {
                        "status": "BLOCKED",
                        "output": None,
                        "scan_threat_level": scan_result.threat_level.value,
                        "drift_score": drift_result.drift_score,
                        "drift_type": drift_result.drift_type.value,
                        "reason": drift_result.explanation,
                        "session_id": intent.task_id,
                        "scan_id": scan_result.scan_id,
                        "user_decision": drift_decision.value,
                    }

        return {
            "status": "OK",
            "output": agent_output,
            "scan_threat_level": scan_result.threat_level.value,
            "drift_score": drift_result.drift_score if drift_result else 0.0,
            "drift_type": drift_result.drift_type.value if drift_result else "ALIGNED",
            "session_id": intent.task_id,
            "scan_id": scan_result.scan_id,
            "user_decision": user_decision.value if user_decision else None,
            "alert": alert_info,
        }

    def _trigger_background_evolution(self):
        """Asynchronously triggers the system self-evolution in a background thread."""
        import threading
        from core.evolution import evolve
        
        def run_evolve():
            try:
                evolve()
            except Exception as e:
                logger.error("Background auto-evolution failed: %s", e)

        thread = threading.Thread(target=run_evolve, daemon=True)
        thread.start()

    def wrap(self, task_extractor: Optional[Callable[..., str]] = None):
        """
        A decorator to wrap any existing AI agent function.
        Automatically intercepts arguments, runs GuardRail checks, and returns the result.
        
        Example:
            @guardrail.wrap()
            def my_agent(task, document):
                return llm(task, document)
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Bind function arguments to inspect them
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()

                # Extract task and content from arguments
                task = None
                content = None

                # 1. Use custom extractor if provided
                if task_extractor:
                    try:
                        task = task_extractor(*args, **kwargs)
                    except Exception as e:
                        logger.warning("task_extractor failed: %s", e)

                # 2. Heuristically match by parameter name
                for name, value in bound.arguments.items():
                    name_lower = name.lower()
                    if task is None and name_lower in ["task", "instruction", "prompt", "query"]:
                        task = value
                    elif content is None and name_lower in ["content", "text", "doc", "document", "input_content"]:
                        content = value

                # 3. Fallback to positions if unmatched
                param_values = list(bound.arguments.values())
                if task is None and len(param_values) > 0:
                    task = param_values[0]
                if content is None and len(param_values) > 1:
                    content = param_values[1]

                if not task or not content:
                    raise ValueError(
                        f"Could not automatically extract 'task' and 'content' parameters for guardrail from function '{func.__name__}'. "
                        "Please pass a custom task_extractor or rename your parameters to 'task' and 'content'."
                    )

                # Standardize inputs to string
                task_str = str(task)
                content_str = str(content)

                # Wrap original function as the agent_callable
                async def custom_agent(t, c):
                    # Rebind and invoke original function with the sanitized content
                    for name in bound.arguments:
                        name_lower = name.lower()
                        if name_lower in ["content", "text", "doc", "document", "input_content"]:
                            bound.arguments[name] = c
                        elif name_lower in ["task", "instruction", "prompt", "query"]:
                            bound.arguments[name] = t
                    
                    # If position-based fallback was used, replace second positional argument with content
                    param_keys = list(bound.arguments.keys())
                    if len(param_keys) > 1 and bound.arguments[param_keys[1]] == content:
                        bound.arguments[param_keys[1]] = c
                    
                    if inspect.iscoroutinefunction(func):
                        return await func(*bound.args, **bound.kwargs)
                    return func(*bound.args, **bound.kwargs)

                # Run the GuardRail wrapper pipeline
                result = await self.run(
                    task=task_str,
                    input_content=content_str,
                    agent_callable=custom_agent
                )
                return result

            return wrapper
        return decorator


guardrail = GuardRail(decision_mode="api")
