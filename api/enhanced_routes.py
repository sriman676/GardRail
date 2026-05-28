"""Enhanced API endpoints for better system management."""
import logging
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel, Field
from typing import Optional

from core.rule_manager import promote_staged_to_active, get_active_rules, get_staged_rules
from db.audit_log import AuditLog
from core.auth import require_admin_api_key
from config import settings
from core import metrics

logger = logging.getLogger("guardrail.enhanced_routes")
router = APIRouter()
audit = AuditLog()


class RulePromotionResponse(BaseModel):
    """Response for rule promotion operation."""
    success: bool = Field(description="Whether promotion succeeded")
    message: str = Field(description="Promotion result message")
    rules_promoted: int = Field(description="Number of rules promoted")


@router.post("/rules/promote")
async def promote_rules(admin: bool = Depends(require_admin_api_key)) -> RulePromotionResponse:
    """
    Promote staged rules to active injection rules.
    
    This endpoint takes all rules in the staging area and appends them to the
    active rule set, avoiding duplicates by pattern + pattern_id.
    
    Requires admin API key authentication.
    
    Returns:
        RulePromotionResponse: Result of promotion operation
        
    Raises:
        HTTPException: 401 if unauthorized, 500 if promotion fails
    """
    try:
        success = promote_staged_to_active()
        if success:
            staged_rules = get_staged_rules()
            # Update metrics
            metrics.active_rules_count.set(len(get_active_rules().get("rules", [])))
            metrics.staged_rules_count.set(len(staged_rules.get("rules", [])))
            return RulePromotionResponse(
                success=True,
                message="Staged rules successfully promoted to active",
                rules_promoted=len(staged_rules.get("rules", []))
            )
        else:
            return RulePromotionResponse(
                success=False,
                message="No staged rules to promote",
                rules_promoted=0
            )
    except Exception as e:
        logger.error(f"Rule promotion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Promotion failed: {str(e)}")


class SystemStats(BaseModel):
    """System-wide statistics."""
    total_scans: int = Field(description="Total scans performed")
    attacks_blocked: int = Field(description="Dangerous threats detected")
    suspicious_scans: int = Field(description="Suspicious scans")
    safe_scans: int = Field(description="Safe scans")
    drift_violations: int = Field(description="Behavioral drift violations")
    active_rules: int = Field(description="Active injection rules")
    staged_rules: int = Field(description="Staged injection rules")
    drift_threshold: float = Field(description="Current drift threshold")


@router.get("/stats/summary")
async def system_stats(x_tenant_id: str = Header("default", alias="X-Tenant-Id")) -> SystemStats:
    """
    Get system-wide statistics summary.
    
    Returns aggregate statistics for scans, threats, rules, and configuration
    across all audit data for the specified tenant.
    
    Args:
        x_tenant_id: Tenant ID for multi-tenant isolation (default: 'default')
        
    Returns:
        SystemStats: Comprehensive system statistics
    """
    try:
        stats = audit.get_stats(tenant_id=x_tenant_id)
        active = get_active_rules()
        staged = get_staged_rules()
        
        return SystemStats(
            total_scans=stats.get("total_scans", 0),
            attacks_blocked=stats.get("attacks_blocked", 0),
            suspicious_scans=stats.get("suspicious", 0),
            safe_scans=stats.get("safe_scans", 0),
            drift_violations=stats.get("drift_violations", 0),
            active_rules=len(active.get("rules", [])),
            staged_rules=len(staged.get("rules", [])),
            drift_threshold=settings.DRIFT_THRESHOLD
        )
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve statistics")


class AlertRecord(BaseModel):
    """A single alert record from history."""
    id: str = Field(description="Unique alert ID")
    scan_id: str = Field(description="Associated scan ID")
    threat_level: str = Field(description="Threat level (SAFE, SUSPICIOUS, DANGER)")
    decision: Optional[str] = Field(description="User decision (BLOCK, ALLOW_ONCE, REPORT)")
    timestamp: str = Field(description="ISO timestamp")


@router.get("/alerts/history")
async def alert_history(
    limit: int = Query(50, ge=1, le=1000),
    x_tenant_id: str = Header("default", alias="X-Tenant-Id")
) -> dict:
    """
    Get alert history for the tenant.
    
    Returns recent alerts with user decisions in reverse chronological order.
    
    Args:
        limit: Maximum number of records to return (1-1000, default 50)
        x_tenant_id: Tenant ID for multi-tenant isolation
        
    Returns:
        dict: Alerts list and total count
    """
    try:
        entries = audit.get_recent(limit=limit, tenant_id=x_tenant_id)
        alerts = []
        for entry in entries:
            if "scan_id" in entry:
                alerts.append({
                    "id": entry.get("id", ""),
                    "scan_id": entry.get("scan_id", ""),
                    "threat_level": entry.get("threat_level", "UNKNOWN"),
                    "decision": entry.get("user_decision"),
                    "timestamp": entry.get("created_at", "")
                })
        return {"alerts": alerts, "total": len(alerts)}
    except Exception as e:
        logger.error(f"Failed to get alert history: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve alert history")


class ConfigSnapshot(BaseModel):
    """Current system configuration snapshot."""
    drift_threshold: float = Field(description="Drift detection threshold")
    llm_provider: str = Field(description="Active LLM provider")
    llm_model: Optional[str] = Field(description="Active LLM model")
    rate_limit_max_requests: int = Field(description="Rate limit max requests")
    rate_limit_window_seconds: int = Field(description="Rate limit time window")
    db_path: str = Field(description="Database file path")


@router.get("/config/get")
async def get_config(admin: bool = Depends(require_admin_api_key)) -> ConfigSnapshot:
    """
    Get current system configuration.
    
    Returns the active configuration for GuardRail settings.
    Requires admin authentication.
    
    Returns:
        ConfigSnapshot: Current configuration values
    """
    return ConfigSnapshot(
        drift_threshold=settings.DRIFT_THRESHOLD,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        rate_limit_max_requests=200,
        rate_limit_window_seconds=60,
        db_path=settings.GUARDRAIL_DB_PATH
    )


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    drift_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    llm_provider: Optional[str] = Field(None)


@router.post("/config/update")
async def update_config(
    update: ConfigUpdate,
    admin: bool = Depends(require_admin_api_key)
) -> dict:
    """
    Update system configuration.
    
    Allows dynamic configuration updates without restart.
    Only fields provided will be updated; others remain unchanged.
    Requires admin authentication.
    
    Args:
        update: Configuration fields to update
        admin: Admin authentication (via dependency)
        
    Returns:
        dict: Update result and new config state
    """
    changes = {}
    try:
        if update.drift_threshold is not None:
            settings.DRIFT_THRESHOLD = update.drift_threshold
            metrics.drift_threshold_gauge.set(update.drift_threshold)
            changes["drift_threshold"] = update.drift_threshold
            logger.info(f"Updated drift_threshold to {update.drift_threshold}")
        
        if update.llm_provider is not None:
            settings.LLM_PROVIDER = update.llm_provider
            changes["llm_provider"] = update.llm_provider
            logger.info(f"Updated LLM_PROVIDER to {update.llm_provider}")
        
        return {
            "success": True,
            "message": f"Updated {len(changes)} config values",
            "changes": changes
        }
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/health/detailed")
async def health_detailed() -> dict:
    """
    Get detailed system health check with component status.
    
    Provides comprehensive health information for all system components
    including database, LLM provider, and middleware.
    
    Returns:
        dict: Detailed health status for all components
    """
    try:
        # Database check
        db_ok = True
        db_error = None
        try:
            audit.get_recent(limit=1)
        except Exception as e:
            db_ok = False
            db_error = str(e)
        
        # OpenAI check (cached)
        openai_ok = True
        openai_error = None
        try:
            from core.openai_client import create_openai_client
            client = create_openai_client()
            client.models.list()
        except Exception as e:
            openai_ok = False
            openai_error = str(e)
        
        # Load rules
        try:
            from core.rule_manager import get_active_rules, get_staged_rules
            active_rules = len(get_active_rules().get("rules", []))
            staged_rules = len(get_staged_rules().get("rules", []))
        except Exception:
            active_rules = 0
            staged_rules = 0
        
        overall_status = "healthy" if (db_ok and openai_ok) else "degraded"
        
        return {
            "status": overall_status,
            "version": "1.0.0",
            "components": {
                "database": {
                    "status": "ok" if db_ok else "error",
                    "error": db_error
                },
                "llm_provider": {
                    "status": "ok" if openai_ok else "error",
                    "provider": settings.LLM_PROVIDER,
                    "error": openai_error
                },
                "rules": {
                    "active_count": active_rules,
                    "staged_count": staged_rules
                },
                "configuration": {
                    "drift_threshold": settings.DRIFT_THRESHOLD,
                    "log_level": settings.LOG_LEVEL
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "components": {}
        }
