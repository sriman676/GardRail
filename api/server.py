import logging
import uuid
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes import router
from api.enhanced_routes import router as enhanced_router
from config import settings
from core.metrics import metrics_latest, CONTENT_TYPE_LATEST, request_latency
from core.middleware import RateLimitMiddleware, CircuitBreakerMiddleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)

logger = logging.getLogger("guardrail.server")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request correlation ID for distributed tracing."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start_time = time.time()
        response = await call_next(request)
        latency = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        request_latency.observe(latency)
        return response

app = FastAPI(
    title="GuardRail API",
    version="1.0.0",
    description="Real-Time Prompt Injection Shield for AI Agents",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add middleware in reverse order (first added = last executed)
app.add_middleware(RequestIDMiddleware)  # Outermost: capture request ID early
app.add_middleware(RateLimitMiddleware, max_requests=200, window=60)
app.add_middleware(CircuitBreakerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "x-tenant-id", "x-api-key", "x-request-id"],
)

app.include_router(router)
app.include_router(enhanced_router)
app.mount("/ui", StaticFiles(directory="ui"), name="ui")


@app.get("/metrics")
def metrics():
    try:
        data = metrics_latest()
        return Response(data, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        return Response(b"", media_type="text/plain")


@app.get("/")
def root():
    """Redirect root path to Swagger UI documentation."""
    return RedirectResponse(url="/docs", status_code=301)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.GUARDRAIL_HOST, port=settings.GUARDRAIL_PORT)
