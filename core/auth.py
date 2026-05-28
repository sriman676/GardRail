import os
from typing import List

from fastapi import Header, HTTPException

from config import settings


def _load_admin_keys() -> List[str]:
    """
    Load admin API keys from environment variables.
    
    Admin keys are read from the ADMIN_API_KEYS environment variable,
    which should be a comma-separated list of allowed keys.
    
    Returns:
        List[str]: List of valid admin API keys, empty if none configured
    """
    # ADMIN_API_KEYS can be a comma-separated list in the environment
    keys = os.environ.get("ADMIN_API_KEYS") or ""
    if keys:
        return [k.strip() for k in keys.split(",") if k.strip()]
    # fallback to settings if present
    return []


def require_admin_api_key(x_api_key: str = Header(default=None)):
    """
    FastAPI dependency to validate admin API key.
    
    Validates that the X-API-Key header contains a valid admin key.
    Used as a dependency on protected endpoints like /evolve, /audit/reset.
    
    Args:
        x_api_key: The X-API-Key header value from the request
        
    Returns:
        bool: True if valid, raises HTTPException otherwise
        
    Raises:
        HTTPException: 403 if no keys configured, 401 if key invalid/missing
    """
    admin_keys = _load_admin_keys()
    if not admin_keys:
        # If no admin keys configured, disallow the operation for safety
        raise HTTPException(status_code=403, detail="Admin API access not configured.")

    if not x_api_key or x_api_key not in admin_keys:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-KEY header.")

    return True
