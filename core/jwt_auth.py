"""JWT token authentication utilities."""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Header
from enum import Enum

logger = logging.getLogger("guardrail.jwt_auth")

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))


class TokenScope(str, Enum):
    """Token permission scopes."""
    READ = "read"          # Read audit logs, metrics, config
    WRITE = "write"        # Write config updates
    ADMIN = "admin"        # Full administrative access


class JWTAuthError(Exception):
    """JWT authentication error."""
    pass


def create_token(subject: str, scopes: list[str] = None, expires_in_hours: int = JWT_EXPIRATION_HOURS) -> str:
    """
    Create a JWT token.
    
    Args:
        subject: Token subject (user/service identifier)
        scopes: List of permission scopes
        expires_in_hours: Token expiration time in hours
        
    Returns:
        str: Encoded JWT token
    """
    if scopes is None:
        scopes = [TokenScope.READ.value]
    
    now = datetime.utcnow()
    exp = now + timedelta(hours=expires_in_hours)
    
    payload = {
        "sub": subject,
        "scopes": scopes,
        "iat": now,
        "exp": exp
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.info(f"Created JWT token for subject={subject} with scopes={scopes}")
    return token


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict: Token payload
        
    Raises:
        JWTAuthError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise JWTAuthError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise JWTAuthError("Invalid token")


def verify_token_scope(token: str, required_scope: str) -> Dict[str, Any]:
    """
    Verify token and check for required scope.
    
    Args:
        token: JWT token string
        required_scope: Required permission scope
        
    Returns:
        Dict: Token payload
        
    Raises:
        JWTAuthError: If token invalid, expired, or lacking required scope
    """
    payload = verify_token(token)
    scopes = payload.get("scopes", [])
    
    if required_scope not in scopes and TokenScope.ADMIN.value not in scopes:
        logger.warning(f"Token lacks required scope: {required_scope}")
        raise JWTAuthError(f"Token lacks required scope: {required_scope}")
    
    return payload


def require_jwt_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    FastAPI dependency to require valid JWT token.
    
    Token can be provided as:
    - Authorization: Bearer <token>
    - X-Token: <token>
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Dict: Token payload
        
    Raises:
        HTTPException: If token missing or invalid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    # Handle "Bearer <token>" format
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        token = authorization  # Allow raw token
    
    try:
        return verify_token(token)
    except JWTAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_jwt_scope(required_scope: str):
    """
    Create a FastAPI dependency that requires a specific JWT scope.
    
    Args:
        required_scope: Required permission scope
        
    Returns:
        Dependency function
    """
    def dependency(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization token")
        
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            token = authorization
        
        try:
            return verify_token_scope(token, required_scope)
        except JWTAuthError as e:
            raise HTTPException(status_code=403, detail=str(e))
    
    return dependency
