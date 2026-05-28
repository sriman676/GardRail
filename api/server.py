import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response

from api.routes import router
from config import settings
from core.metrics import metrics_latest, CONTENT_TYPE_LATEST
from core.middleware import RateLimitMiddleware, CircuitBreakerMiddleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)

app = FastAPI(title="GuardRail API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "x-tenant-id", "x-api-key"],
)
app.add_middleware(CircuitBreakerMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=200, window=60)
app.include_router(router)
app.mount("/ui", StaticFiles(directory="ui"), name="ui")


@app.get("/metrics")
def metrics():
    try:
        data = metrics_latest()
        return Response(data, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        return Response(b"", media_type="text/plain")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.GUARDRAIL_HOST, port=settings.GUARDRAIL_PORT)
