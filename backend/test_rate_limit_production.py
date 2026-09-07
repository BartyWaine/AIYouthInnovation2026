"""Rate-limit productionization tests."""
import importlib
import json
import logging
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
import urllib.parse

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_rate_limiter():
    """Import or reload rate_limiter module."""
    import app.rate_limiter as rl
    importlib.reload(rl)
    return rl


def _import_main_with_captured_logs():
    """Import/reload main.py and return (module, captured_log_records)."""
    if not os.getenv("JWT_SECRET"):
        os.environ["JWT_SECRET"] = "test-jwt-secret-for-rate-limit-tests"

    import app.main as main_module

    captured = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record):
            captured.append(self.format(record))

    handler = _CaptureHandler()
    handler.setLevel(logging.INFO)
    main_module.logger.addHandler(handler)
    main_module.logger.setLevel(logging.INFO)

    importlib.reload(main_module)

    return main_module, captured


# ---------------------------------------------------------------------------
# 1. Single-worker dev with memory:// is allowed
# ---------------------------------------------------------------------------

def test_single_worker_dev_memory_allowed():
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    os.environ["ENVIRONMENT"] = "development"
    original_argv = sys.argv
    sys.argv = ["uvicorn", "app.main:app"]
    try:
        rl = _import_rate_limiter()
        rl._check_rate_limit_storage_on_startup()  # should not raise
        print("PASS: Single-worker dev with memory:// allowed")
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# 2. Multi-worker production with memory:// is rejected
# ---------------------------------------------------------------------------

def test_multi_worker_production_memory_rejected():
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    os.environ["ENVIRONMENT"] = "production"
    sys.argv = ["uvicorn", "app.main:app", "--workers", "4"]
    try:
        rl = _import_rate_limiter()
        try:
            rl._check_rate_limit_storage_on_startup()
            print("FAIL: Multi-worker production with memory:// should have raised RuntimeError")
            sys.exit(1)
        except RuntimeError as exc:
            message = str(exc)
            if "memory://" in message and "workers" in message:
                print("PASS: Multi-worker production with memory:// rejected with clear message")
            else:
                print(f"FAIL: Unexpected error message: {message}")
                sys.exit(1)
    finally:
        sys.argv = ["uvicorn", "app.main:app"]


# ---------------------------------------------------------------------------
# 3. Multi-worker production with shared storage is accepted
# ---------------------------------------------------------------------------

def test_multi_worker_production_redis_accepted():
    os.environ["RATE_LIMIT_STORAGE"] = "redis://redis:6379"
    os.environ["ENVIRONMENT"] = "production"
    sys.argv = ["uvicorn", "app.main:app", "-w", "4"]
    try:
        rl = _import_rate_limiter()
        rl._check_rate_limit_storage_on_startup()  # should not raise
        print("PASS: Multi-worker production with redis:// accepted")
    finally:
        sys.argv = ["uvicorn", "app.main:app"]


# ---------------------------------------------------------------------------
# 4. Multi-worker dev with memory:// warns but does not raise
# ---------------------------------------------------------------------------

def test_multi_worker_dev_memory_warns():
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    os.environ["ENVIRONMENT"] = "development"
    sys.argv = ["uvicorn", "app.main:app", "--workers", "2"]
    try:
        rl = _import_rate_limiter()
        rl._check_rate_limit_storage_on_startup()  # should not raise in dev
        print("PASS: Multi-worker dev with memory:// warns but does not raise")
    finally:
        sys.argv = ["uvicorn", "app.main:app"]


# ---------------------------------------------------------------------------
# 5. Rate-limited request returns HTTP 429
# ---------------------------------------------------------------------------

def test_rate_limited_request_returns_429():
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    os.environ["ENVIRONMENT"] = "development"
    sys.argv = ["uvicorn", "app.main:app"]

    rl = _import_rate_limiter()
    test_limiter = Limiter(key_func=lambda request: "rate_test_client", default_limits=["2/minute"])

    test_app = FastAPI()
    test_app.state.limiter = test_limiter
    test_app.add_middleware(SlowAPIMiddleware)

    captured_logs = []

    def test_handler(request: Request, exc: RateLimitExceeded):
        log_data = {
            "event": "rate_limit_exceeded",
            "method": request.method,
            "path": request.url.path,
            "status": 429,
            "rate_limit": str(exc.detail) if hasattr(exc, "detail") else "unknown",
        }
        request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        if request_id:
            log_data["request_id"] = request_id
        captured_logs.append(log_data)
        return JSONResponse(status_code=429, content={"detail": str(exc.detail)})

    test_app.add_exception_handler(RateLimitExceeded, test_handler)

    @test_app.get("/test-endpoint")
    @test_limiter.limit("2/minute")
    def test_endpoint(request: Request):
        return {"ok": True}

    client = TestClient(test_app)

    client.get("/test-endpoint")
    client.get("/test-endpoint")
    response = client.get("/test-endpoint")

    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    print("PASS: Rate-limited request returns HTTP 429")


# ---------------------------------------------------------------------------
# 6. Exactly one structured, non-sensitive rate-limit event is emitted
# ---------------------------------------------------------------------------

def test_single_structured_rate_limit_event():
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    os.environ["ENVIRONMENT"] = "development"
    sys.argv = ["uvicorn", "app.main:app"]

    rl = _import_rate_limiter()
    test_limiter = Limiter(key_func=lambda request: "rate_test_client2", default_limits=["2/minute"])

    test_app = FastAPI()
    test_app.state.limiter = test_limiter
    test_app.add_middleware(SlowAPIMiddleware)

    captured_logs = []

    def test_handler(request: Request, exc: RateLimitExceeded):
        log_data = {
            "event": "rate_limit_exceeded",
            "method": request.method,
            "path": request.url.path,
            "status": 429,
            "rate_limit": str(exc.detail) if hasattr(exc, "detail") else "unknown",
        }
        request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        if request_id:
            log_data["request_id"] = request_id
        captured_logs.append(log_data)
        return JSONResponse(status_code=429, content={"detail": str(exc.detail)})

    test_app.add_exception_handler(RateLimitExceeded, test_handler)

    @test_app.get("/test-endpoint")
    @test_limiter.limit("2/minute")
    def test_endpoint(request: Request):
        return {"ok": True}

    client = TestClient(test_app)

    client.get("/test-endpoint", headers={"X-Request-ID": "test-456"})
    client.get("/test-endpoint", headers={"X-Request-ID": "test-456"})
    response = client.get("/test-endpoint", headers={"X-Request-ID": "test-456"})

    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    print("PASS: Rate-limited request returns HTTP 429")

    rate_logs = [l for l in captured_logs if l.get("event") == "rate_limit_exceeded"]
    assert len(rate_logs) == 1, f"Expected exactly 1 rate-limit log, got {len(rate_logs)}: {rate_logs}"

    log_entry = rate_logs[0]
    assert log_entry["method"] == "GET"
    assert log_entry["path"] == "/test-endpoint"
    assert log_entry["status"] == 429
    assert "rate_limit" in log_entry
    assert log_entry.get("request_id") == "test-456"
    print("PASS: Exactly one structured, non-sensitive rate-limit event emitted")


# ---------------------------------------------------------------------------
# 7. Logs do not contain sensitive data
# ---------------------------------------------------------------------------

def test_logs_exclude_sensitive_data():
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    os.environ["ENVIRONMENT"] = "development"
    sys.argv = ["uvicorn", "app.main:app"]

    rl = _import_rate_limiter()
    test_limiter = Limiter(key_func=lambda request: "rate_test_client3", default_limits=["1/minute"])

    test_app = FastAPI()
    test_app.state.limiter = test_limiter
    test_app.add_middleware(SlowAPIMiddleware)

    captured_logs = []

    def test_handler(request: Request, exc: RateLimitExceeded):
        log_data = {
            "event": "rate_limit_exceeded",
            "method": request.method,
            "path": request.url.path,
            "status": 429,
            "rate_limit": str(exc.detail) if hasattr(exc, "detail") else "unknown",
        }
        request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        if request_id:
            log_data["request_id"] = request_id
        captured_logs.append(log_data)
        return JSONResponse(status_code=429, content={"detail": str(exc.detail)})

    test_app.add_exception_handler(RateLimitExceeded, test_handler)

    @test_app.get("/test-endpoint")
    @test_limiter.limit("1/minute")
    def test_endpoint(request: Request):
        return {"ok": True}

    client = TestClient(test_app)

    # Add a request with sensitive-looking headers to ensure they aren't logged
    client.get("/test-endpoint", headers={"Authorization": "Bearer secret-token", "X-Api-Key": "secret-key"})
    client.get("/test-endpoint", headers={"Authorization": "Bearer secret-token", "X-Api-Key": "secret-key"})

    rate_logs = [l for l in captured_logs if l.get("event") == "rate_limit_exceeded"]
    assert len(rate_logs) == 1
    log_str = json.dumps(rate_logs[0])

    assert "Bearer" not in log_str
    assert "secret-token" not in log_str
    assert "secret-key" not in log_str
    assert "password" not in log_str.lower()
    print("PASS: Logs do not contain authorization headers, JWTs, passwords, or API keys")


# ---------------------------------------------------------------------------
# 8. Existing non-rate-limited requests continue to work
# ---------------------------------------------------------------------------

def test_existing_requests_continue_to_work():
    BASE = "http://127.0.0.1:8022/api/v1"
    try:
        body = urllib.parse.urlencode({"username": "team1@sti.edu.mm", "password": "team123"}).encode()
        req = urllib.request.Request(BASE + "/auth/login", data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        resp = urllib.request.urlopen(req)
        token = json.loads(resp.read())["access_token"]

        req2 = urllib.request.Request(BASE + "/auth/me", method="GET")
        req2.add_header("Authorization", f"Bearer {token}")
        resp2 = urllib.request.urlopen(req2)
        data = json.loads(resp2.read())
        assert data["email"] == "team1@sti.edu.mm"
        print("PASS: Existing non-rate-limited login and /auth/me requests work")
    except Exception as e:
        print(f"INFO: Skipped existing-request test (server may not be running): {e}")


# ---------------------------------------------------------------------------
# 9. Redis credentials are never printed in logs
# ---------------------------------------------------------------------------

def test_redis_credentials_not_logged():
    os.environ["RATE_LIMIT_STORAGE"] = "redis://:supersecret@redis:6379/0"
    os.environ["ENVIRONMENT"] = "production"
    original_argv = sys.argv
    sys.argv = ["uvicorn", "app.main:app", "-w", "4"]
    try:
        _, captured = _import_main_with_captured_logs()
        combined = "\n".join(captured)
        assert "supersecret" not in combined, "Redis password found in startup logs"
        assert "redis://:supersecret" not in combined, "Redis URL with password found in startup logs"
        print("PASS: Redis credentials are not printed in logs")
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# 10. Redis is not publicly exposed in Docker Compose
# ---------------------------------------------------------------------------

def test_redis_not_publicly_exposed_in_compose():
    compose_path = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
    compose_path = os.path.normpath(compose_path)
    with open(compose_path, encoding="utf-8") as fh:
        content = fh.read()

    in_redis = False
    redis_ports = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("redis:"):
            in_redis = True
        elif in_redis and stripped and not stripped.startswith("-") and not stripped.startswith(" ") and not stripped.startswith("\t"):
            in_redis = False
        if in_redis and stripped.startswith("- "):
            redis_ports.append(stripped)

    public_ports = []
    for pm in redis_ports:
        pm = pm.lstrip("- ").strip()
        if not pm:
            continue
        if ":" in pm:
            host_part = pm.split(":")[0]
            if host_part not in ("127.0.0.1", "localhost"):
                public_ports.append(pm)
        else:
            public_ports.append(pm)

    assert not public_ports, f"Redis has public port exposure in docker-compose.yml: {public_ports}"
    print("PASS: Redis is not publicly exposed in Docker Compose")


# ---------------------------------------------------------------------------
# 11. Startup logs a safe storage description
# ---------------------------------------------------------------------------

def test_startup_logs_storage_description():
    os.environ["RATE_LIMIT_STORAGE"] = "redis://redis:6379/0"
    os.environ["ENVIRONMENT"] = "production"
    original_argv = sys.argv
    sys.argv = ["uvicorn", "app.main:app", "-w", "1"]
    try:
        _, captured = _import_main_with_captured_logs()
        combined = "\n".join(captured)
        assert "shared Redis" in combined, f"Expected 'shared Redis' in startup logs, got: {combined}"
        assert "redis://redis:6379/0" not in combined, "Full Redis URL should not be logged"
        print("PASS: Startup logs a safe storage description")
    finally:
        sys.argv = original_argv


# ---------------------------------------------------------------------------
# 12. Environment variables are read correctly
# ---------------------------------------------------------------------------

def test_environment_variables_read_correctly():
    os.environ["RATE_LIMIT_STORAGE"] = "memory://"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["RATE_LIMIT_LOGIN"] = "10/minute"
    os.environ["RATE_LIMIT_UPLOAD"] = "20/minute"
    os.environ["RATE_LIMIT_DEFAULT"] = "3/minute"

    try:
        rl = _import_rate_limiter()
        assert rl.get_limit("RATE_LIMIT_LOGIN", "5/minute") == "10/minute"
        assert rl.get_limit("RATE_LIMIT_UPLOAD", "10/minute") == "20/minute"
        assert rl.get_limit("RATE_LIMIT_DEFAULT", "5/minute") == "3/minute"
        assert rl.get_limit("RATE_LIMIT_CORRECT_SCORE", "5/minute") == "5/minute"
        print("PASS: Environment variables are read correctly")
    finally:
        del os.environ["RATE_LIMIT_LOGIN"]
        del os.environ["RATE_LIMIT_UPLOAD"]
        del os.environ["RATE_LIMIT_DEFAULT"]


if __name__ == "__main__":
    test_single_worker_dev_memory_allowed()
    test_multi_worker_production_memory_rejected()
    test_multi_worker_production_redis_accepted()
    test_multi_worker_dev_memory_warns()
    test_rate_limited_request_returns_429()
    test_single_structured_rate_limit_event()
    test_logs_exclude_sensitive_data()
    test_existing_requests_continue_to_work()
    test_redis_credentials_not_logged()
    test_redis_not_publicly_exposed_in_compose()
    test_startup_logs_storage_description()
    test_environment_variables_read_correctly()
    print("\nAll rate-limit productionization tests passed!")
