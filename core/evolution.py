import os
import re
import logging
from typing import Dict, Any, List

from config import settings
from db.audit_log import AuditLog
from core.llm_client import GenericLLMClient

logger = logging.getLogger("guardrail.evolution")


EVOLUTION_ANALYSIS_PROMPT = """You are the Meta-Optimizer for the GuardRail AI Security Shield.

Your job is to analyze historical database logs and optimize the system's security detection rules and thresholds.
Below is a summary of historical data from the audit database:

--- HISTORICAL LOG ENTRIES ---
{log_entries}
------------------------------

Current Settings:
- Drift Threshold: {current_threshold}

Analyze the logs for:
1. False Positives (DANGER triggers where the user decided "ALLOW_ONCE") -> Indicates scanning is too aggressive or the drift threshold is too low.
2. False Negatives / Escaped Injections (Scans marked SAFE/SUSPICIOUS, but later triggered HIGH DRIFT >= 0.70 or required manual BLOCK) -> Indicates prompt injections slipped past our regex rules.

Recommend:
1. An optimized "drift_threshold" (float between 0.50 and 0.95). If the false positive rate is high, recommend raising it slightly. If threats slipped past, recommend lowering it slightly.
2. "new_regex_rules": A list of new, clean regex patterns to add to our scanner to capture prompt injection keywords or structures that slipped through.
   Format for each rule must be a JSON object:
   {{
     "pattern": "valid python regex string",
     "pattern_id": "EVOLVED_xxx" (incrementing ID),
     "explanation": "Brief description of what it catches"
   }}

Respond ONLY with valid JSON with the following exact keys:
{{
  "drift_threshold": float,
  "new_regex_rules": [
     {{
       "pattern": "string",
       "pattern_id": "string",
       "explanation": "string"
     }}
  ],
  "rationale": "One sentence explanation of the optimization"
}}

Respond with valid JSON only. No markdown. No code fences. No explanation."""


class SystemOptimizer:
    """
    Self-Evolving System optimizer for GuardRail.
    Queries the audit log database, runs AI evaluation of historical decisions,
    and automatically adjusts the drift threshold (.env) and appends new regex rules.
    """

    def __init__(self):
        self.audit = AuditLog()
        self.client = GenericLLMClient()

    def evolve(self) -> Dict[str, Any]:
        """
        Runs the self-evolution loop. Parses history, generates AI enhancements,
        auto-tunes settings, and returns the optimization results.
        """
        logger.info("Starting System Optimization & Self-Evolution...")
        
        # 1. Fetch audit logs
        sessions = self.audit.get_recent(limit=30)
        stats = self.audit.get_stats()

        if not sessions:
            logger.info("Self-evolution skipped: Not enough audit logs in database.")
            return {
                "status": "skipped",
                "reason": "Insufficient audit logs in database to perform evolution."
            }

        # 2. Extract drift events to analyze
        drift_events = []
        try:
            with self.audit._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM drift_events ORDER BY created_at DESC LIMIT 30"
                ).fetchall()
                drift_events = [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Could not fetch drift events: %s", e)

        # 3. Format logs for LLM analysis
        formatted_logs = f"Stats: {stats}\n\nRecent Scans:\n"
        for s in sessions[:15]:
            formatted_logs += (
                f"- ScanID: {s['id']} | Threat: {s['threat_level']} | "
                f"Decision: {s['user_decision']} | Created: {s['created_at']}\n"
            )
        
        formatted_logs += "\nRecent Drift Events:\n"
        for d in drift_events[:15]:
            formatted_logs += (
                f"- DriftID: {d['id']} | Action: {d['agent_action'][:100]} | "
                f"Score: {d['drift_score']} | Type: {d['drift_type']} | Evolve: {d['triggered']}\n"
            )

        # 4. Request Meta-Optimization recommendations
        fallback_default = {
            "drift_threshold": settings.DRIFT_THRESHOLD,
            "new_regex_rules": [],
            "rationale": "No optimization applied due to processing fallback."
        }

        recommendations = self.client.generate(
            prompt=EVOLUTION_ANALYSIS_PROMPT.format(
                log_entries=formatted_logs,
                current_threshold=settings.DRIFT_THRESHOLD
            ),
            json_format=True,
            temperature=0.2,
            max_tokens=600,
            fallback_default=fallback_default
        )

        # 5. Apply recommendations
        threshold_changed = False
        rules_added = 0

        # A. Apply drift threshold optimization to the .env file
        new_threshold = recommendations.get("drift_threshold", settings.DRIFT_THRESHOLD)
        # Constrain threshold range
        new_threshold = max(0.50, min(0.95, float(new_threshold)))
        
        if abs(new_threshold - settings.DRIFT_THRESHOLD) >= 0.01:
            threshold_changed = self._update_env_threshold(new_threshold)
            if threshold_changed:
                settings.DRIFT_THRESHOLD = new_threshold

        # B. Apply new regex rules dynamically to core/injection_scanner.py if any
        new_rules = recommendations.get("new_regex_rules", [])
        if new_rules:
            rules_added = self._apply_new_rules(new_rules)

        logger.info(
            "Evolution complete. Threshold updated=%s, Evolved Rules Added=%s. Rationale: %s",
            threshold_changed,
            rules_added,
            recommendations.get("rationale")
        )

        return {
            "status": "completed",
            "threshold_updated": threshold_changed,
            "new_threshold": new_threshold,
            "rules_added": rules_added,
            "rationale": recommendations.get("rationale", ""),
            "applied_rules": new_rules
        }

    def _update_env_threshold(self, threshold: float) -> bool:
        """Helper to write the updated drift threshold back to the .env file."""
        env_path = ".env"
        try:
            if not os.path.exists(env_path):
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(f"DRIFT_THRESHOLD={threshold:.2f}\n")
                return True

            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "DRIFT_THRESHOLD" in content:
                pattern = r"DRIFT_THRESHOLD\s*=\s*[0-9.]+"
                content = re.sub(pattern, f"DRIFT_THRESHOLD={threshold:.2f}", content)
            else:
                content += f"\nDRIFT_THRESHOLD={threshold:.2f}\n"

            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error("Could not write DRIFT_THRESHOLD to .env: %s", e)
            return False

    def _apply_new_rules(self, rules: List[Dict[str, str]]) -> int:
        """
        Helper to append evolved injection patterns dynamically.
        Appends rules to in-memory patterns and writes them to the scanner script.
        """
        scanner_path = "core/injection_scanner.py"
        if not os.path.exists(scanner_path):
            return 0

        added_count = 0
        try:
            with open(scanner_path, "r", encoding="utf-8") as f:
                code = f.read()

            # Find the INJECTION_PATTERNS list in the file
            match = re.search(r"INJECTION_PATTERNS\s*=\s*\[", code)
            if not match:
                return 0

            insert_index = match.end()
            formatted_rules = ""

            from core import injection_scanner

            for r in rules:
                pat = r.get("pattern")
                pid = r.get("pattern_id")
                expl = r.get("explanation")
                
                if not pat or not pid:
                    continue

                # Ensure pattern is valid regex before writing it
                try:
                    re.compile(pat)
                except re.error:
                    logger.warning("Evolved pattern '%s' is not valid python regex. Skipping.", pat)
                    continue

                # Avoid duplicates
                if pid in code or pat in code:
                    continue

                # Append to in-memory module list directly
                injection_scanner.INJECTION_PATTERNS.append((r"{}".format(pat), pid, expl))

                # Build python code string to inject
                # Escape backslashes for string literal insertion
                pat_escaped = pat.replace("\\", "\\\\")
                formatted_rules += f'\n    (\n        r"{pat_escaped}",\n        "{pid}",\n        "{expl}",\n    ),'
                added_count += 1

            if added_count > 0:
                # Write back into the scanner script
                new_code = code[:insert_index] + formatted_rules + code[insert_index:]
                with open(scanner_path, "w", encoding="utf-8") as f:
                    f.write(new_code)

            return added_count
        except Exception as e:
            logger.error("Failed to write evolved regex rules to scanner file: %s", e)
            return 0


# Global shortcut function
def evolve() -> Dict[str, Any]:
    return SystemOptimizer().evolve()
