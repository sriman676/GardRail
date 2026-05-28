import time
import asyncio
from typing import Dict, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

import logging
logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        tenant_id = request.headers.get("x-tenant-id", "default")
        
        # Rate limit by tenant_id + client_ip
        key = f"{tenant_id}:{client_ip}"
        
        now = time.time()
        
        # Clean up old requests
        if key in self.requests:
            self.requests[key] = [t for t in self.requests[key] if now - t < self.window]
        else:
            self.requests[key] = []
            
        if len(self.requests[key]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {key}")
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
            
        self.requests[key].append(now)
        
        return await call_next(request)

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, failure_threshold: int = 5, recovery_timeout: int = 30):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED" # OPEN, HALF_OPEN, CLOSED
        
    async def dispatch(self, request: Request, call_next):
        # We only apply circuit breaker to /run or /scan
        if request.url.path not in ["/run", "/scan", "/evolve"]:
            return await call_next(request)
            
        now = time.time()
        
        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entered HALF_OPEN state")
            else:
                return JSONResponse(status_code=503, content={"detail": "Service unavailable (Circuit Breaker OPEN)"})
                
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                self._record_failure(now)
            else:
                self._record_success()
            return response
        except Exception as e:
            self._record_failure(now)
            raise e
            
    def _record_failure(self, now: float):
        self.failures += 1
        self.last_failure_time = now
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker tripped OPEN after {self.failures} failures")
            
    def _record_success(self):
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failures = 0
            logger.info("Circuit breaker recovered, entered CLOSED state")
        elif self.state == "CLOSED":
            self.failures = max(0, self.failures - 1)
