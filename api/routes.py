import asyncio
import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from agent.guardrail_wrapper import guardrail
from core.alert_manager import UserDecision, alert_manager
from core.injection_scanner import InjectionScanner
from db.audit_log import AuditLog
from core.auth import require_admin_api_key
from core.rule_manager import get_active_rules, get_staged_rules

logger = logging.getLogger("guardrail.api")
router = APIRouter()
audit = AuditLog()

_last_openai_check: float = 0.0
_last_openai_status: bool = True
_OPENAI_CACHE_TTL = 60.0


def _check_openai_cached() -> bool:
    global _last_openai_check, _last_openai_status
    now = time.time()
    if now - _last_openai_check > _OPENAI_CACHE_TTL:
        try:
            from core.openai_client import create_openai_client

            client = create_openai_client()
            client.models.list()
            _last_openai_status = True
        except Exception:
            _last_openai_status = False
        _last_openai_check = now
    return _last_openai_status


class RunRequest(BaseModel):
    task: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class ScanRequest(BaseModel):
    content: str = Field(..., min_length=1)
    use_llm: bool = Field(default=True)


class DecideRequest(BaseModel):
    scan_id: str
    decision: str


@router.post("/run")
async def run(req: RunRequest, x_tenant_id: str = Header("default", alias="X-Tenant-Id")):
    result = await guardrail.run(task=req.task, input_content=req.content, tenant_id=x_tenant_id)
    if result.get("status") == "ERROR":
        raise HTTPException(
            status_code=503,
            detail={
                "error": "openai_unavailable",
                "message": result.get(
                    "reason", "AI service unavailable. Please retry."
                ),
                "status_code": 503,
            },
        )
    return result


@router.post("/scan")
async def scan_only(req: ScanRequest):
    scanner = InjectionScanner()
    result = scanner.scan(req.content, use_llm=req.use_llm)
    import dataclasses

    return {
        "scan_id": result.scan_id,
        "threat_level": result.threat_level.value,
        "matched_patterns": [dataclasses.asdict(p) for p in result.matched_patterns],
        "clean_content": result.clean_content,
        "confidence": result.confidence,
        "llm_explanation": result.llm_explanation,
        "explainability": result.explainability,
    }


@router.post("/alert/decide")
async def decide(req: DecideRequest):
    try:
        decision = UserDecision(req.decision)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Decision must be BLOCK, ALLOW_ONCE, or REPORT"
        )
    alert_manager.submit_decision(decision)
    return {
        "accepted": True,
        "decision": decision.value,
        "message": f"Decision '{decision.value}' submitted.",
    }


@router.get("/audit/log")
async def get_audit_log(limit: int = 50, threat_level: str = None, x_tenant_id: str = Header("default", alias="X-Tenant-Id")):
    entries = audit.get_recent(limit=limit, threat_level=threat_level, tenant_id=x_tenant_id)
    stats = audit.get_stats(tenant_id=x_tenant_id)
    return {"entries": entries, "total": len(entries), "stats": stats}


@router.get("/health")
async def health():
    try:
        audit.get_recent(limit=1)
        db_ok = True
    except Exception:
        db_ok = False
    openai_ok = _check_openai_cached()
    status = "healthy" if (db_ok and openai_ok) else "degraded"
    
    from config import settings
    from core.injection_scanner import INJECTION_PATTERNS
    evolved_count = sum(1 for p in INJECTION_PATTERNS if p[1].startswith("EVOLVED_"))
    
    result = {
        "status": status,
        "version": "1.0.0",
        "db_connected": db_ok,
        "openai_connected": openai_ok,
        "drift_threshold": settings.DRIFT_THRESHOLD,
        "evolved_rules_count": evolved_count,
    }
    if not openai_ok:
        result["warning"] = "OpenAI API unreachable. Pattern-scan-only mode active."
    return result


@router.get("/rules")
async def list_rules():
    try:
        active = get_active_rules()
        staged = get_staged_rules()
        return {"active": active, "staged": staged}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load rules: {e}") from e



@router.post("/audit/reset")
async def audit_reset(admin: bool = Depends(require_admin_api_key), x_tenant_id: str = Header("default", alias="X-Tenant-Id")):
    try:
        audit.reset(tenant_id=x_tenant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}") from e
    return {"reset": True, "message": f"Audit log data cleared for tenant: {x_tenant_id}"}


@router.post("/evolve")
async def trigger_evolution(admin: bool = Depends(require_admin_api_key)):
    from core.evolution import SystemOptimizer
    try:
        # Run evolution in a background thread to prevent blocking the async loop
        loop = asyncio.get_running_loop()
        optimizer = SystemOptimizer()
        result = await loop.run_in_executor(None, optimizer.evolve)
        return result
    except Exception as e:
        logger.error("Self-evolution failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Evolution failed: {str(e)}")



_DEMO_SAMPLES_DIR = Path("tests/attack_samples")

_DEMO_SCENARIOS = [
    {
        "label": "Scenario 1 - Clean Document",
        "task": "Summarize this quarterly report",
        "file": "clean_document.txt",
    },
    {
        "label": "Scenario 2 - Injection Attack",
        "task": "Summarize this employee onboarding guide",
        "file": "priv_injection.txt",
    },
]


@router.post("/demo/run")
async def demo_run():
    results = []
    for scenario in _DEMO_SCENARIOS:
        sample_path = _DEMO_SAMPLES_DIR / scenario["file"]
        if not sample_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Demo sample file not found: {sample_path}. Run from project root.",
            )
        content = sample_path.read_text(encoding="utf-8")
        try:
            outcome = await guardrail.run(task=scenario["task"], input_content=content)
        except asyncio.TimeoutError:
            outcome = {
                "status": "timeout",
                "scan_threat_level": "DANGER",
                "user_decision": "TIMEOUT",
            }

        results.append(
            {
                "label": scenario["label"],
                "task": scenario["task"],
                "threat_level": outcome.get("scan_threat_level", "UNKNOWN"),
                "scan_id": outcome.get("scan_id", ""),
                "decision": outcome.get("user_decision", None),
                "message": (
                    "Document processed cleanly. No threats detected."
                    if outcome.get("scan_threat_level") == "SAFE"
                    else "Prompt injection detected and blocked. Dashboard modal was triggered."
                    if outcome.get("user_decision") not in (None, "TIMEOUT")
                    else "No decision made within 30 seconds. Attack was automatically blocked."
                ),
            }
        )

    return {"status": "completed", "scenarios": results}

from fastapi.responses import PlainTextResponse
import csv
import io

@router.get("/audit/export")
async def export_audit_log(admin: bool = Depends(require_admin_api_key), x_tenant_id: str = Header("default", alias="X-Tenant-Id")):
    """Export recent audit logs as CSV"""
    entries = audit.get_recent(limit=1000, tenant_id=x_tenant_id)
    if not entries:
        return PlainTextResponse("No records found", status_code=204)
        
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=entries[0].keys())
    writer.writeheader()
    for row in entries:
        writer.writerow(row)
        
    return PlainTextResponse(
        output.getvalue(), 
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_export_{x_tenant_id}.csv"}
    )
