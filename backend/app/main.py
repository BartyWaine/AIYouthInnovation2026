import json
import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from .database import Base, engine
from . import models
from .rate_limiter import limiter, _check_rate_limit_storage_on_startup, get_rate_limit_storage_description
from .security import hash_password
from .routers import auth, competitions, teams, submissions, judges, admin
from .routers import validation

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("rate_limit")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------
_check_rate_limit_storage_on_startup()
logger.info("Rate-limit storage configured: %s", get_rate_limit_storage_description())

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Innovation Youth 2026 Competition Platform")

app.state.limiter = limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    log_data = {
        "event": "rate_limit_exceeded",
        "method": request.method,
        "path": request.url.path,
        "status": 429,
        "rate_limit": str(exc.detail) if hasattr(exc, "detail") else "unknown",
        "request_id": request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or "-",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(json.dumps(log_data))

    return JSONResponse(
        status_code=429,
        content={"detail": str(exc.detail)},
        headers={"Retry-After": "60"},
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS configuration – allow frontend origin with credentials
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    allow_origins = ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# Debug route – only available in development
if os.getenv("ENVIRONMENT") != "production":
    @app.get("/debug/routes")
    def list_routes():
        return [route.path for route in app.routes]

# Register routers – all mounted at the generic API base.
app.include_router(auth.router,          prefix="/api/v1")
app.include_router(competitions.router, prefix="/api/v1")
app.include_router(teams.router,        prefix="/api/v1")
app.include_router(submissions.router,  prefix="/api/v1")
app.include_router(judges.router,       prefix="/api/v1")
app.include_router(admin.router,        prefix="/api/v1")
app.include_router(validation.router,   prefix="/api/v1")
