from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .security import hash_password
from .routers import auth, competitions, teams, submissions, judges, admin
from .routers import validation

app = FastAPI(title="AI Innovation Youth 2026 Competition Platform")

# CORS configuration – allow frontend origin with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# Debug route – lists all registered paths (helps confirm routing)
@app.get("/debug/routes")
def list_routes():
    return [route.path for route in app.routes]

# Register routers – all mounted at the generic API base.
# The `auth` router already defines its own "/auth" prefix internally.
app.include_router(auth.router,          prefix="/api/v1")
app.include_router(competitions.router, prefix="/api/v1")
app.include_router(teams.router,        prefix="/api/v1")
app.include_router(submissions.router,  prefix="/api/v1")
app.include_router(judges.router,       prefix="/api/v1")
app.include_router(admin.router,        prefix="/api/v1")
app.include_router(validation.router,   prefix="/api/v1")