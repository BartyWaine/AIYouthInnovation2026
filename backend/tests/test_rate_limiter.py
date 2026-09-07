"""Pytest-based rate limiter tests for AI Youth Innovation 2026."""
import json
import logging
import os
import sys

import pytest

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_test_app(limit_str="2/minute", key="test-client"):
    """Create a small FastAPI app with one rate-limited route."""

    def _key_func(request: Request):
        return key

    test_limiter = Limiter(key_func=_key_func, default_limits=[limit_str])

    app = FastAPI()
    app.state.limiter = test_limiter
    app.add_middleware(SlowAPIMiddleware)

    captured = []

    def handler(request: Request, exc: RateLimitExceeded):
        log_data = {
            "event": "rate_limit_exceeded",
            "method": request.method,
            "path": request.url.path,
            "status": 429,
            "rate_limit": str(exc.detail) if hasattr(exc, "detail") else "unknown",
            "request_id": request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
            or "-",
            "timestamp": __import__("datetime")
            .datetime.now(__import__("datetime").timezone.utc)
            .isoformat(),
        }
        captured.append(log_data)
        return JSONResponse(
            status_code=429,
            content={"detail": str(exc.detail)},
            headers={"Retry-After": "60"},
        )

    app.add_exception_handler(RateLimitExceeded, handler)

    @app.get("/test-endpoint")
    @test_limiter.limit(limit_str)
    def test_endpoint(request: Request):
        return {"ok": True}

    return app, test_limiter, captured


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRateLimit429:
    """Rate-limited request returns HTTP 429 and emits exactly one structured log."""

    def test_429_response_and_single_log_event(self):
        app, _limiter, captured = _build_test_app(limit_str="2/minute")
        client = TestClient(app)

        resp_ok = client.get("/test-endpoint")
        assert resp_ok.status_code == 200

        resp_ok2 = client.get("/test-endpoint")
        assert resp_ok2.status_code == 200

        resp_429 = client.get("/test-endpoint")
        assert resp_429.status_code == 429

        rate_logs = [log for log in captured if log.get("event") == "rate_limit_exceeded"]
        assert len(rate_logs) == 1

        log_entry = rate_logs[0]
        assert log_entry["method"] == "GET"
        assert log_entry["path"] == "/test-endpoint"
        assert log_entry["status"] == 429
        assert "rate_limit" in log_entry
        assert log_entry["request_id"] == "-"
        assert "timestamp" in log_entry

    def test_retry_after_header_present(self):
        app, _limiter, _captured = _build_test_app(limit_str="2/minute")
        client = TestClient(app)

        client.get("/test-endpoint")
        client.get("/test-endpoint")
        resp = client.get("/test-endpoint")
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    def test_correlation_id_propagates_to_log(self):
        app, _limiter, captured = _build_test_app(limit_str="2/minute")
        client = TestClient(app)

        client.get("/test-endpoint", headers={"X-Request-ID": "req-abc-123"})
        client.get("/test-endpoint", headers={"X-Request-ID": "req-abc-123"})
        client.get("/test-endpoint", headers={"X-Request-ID": "req-abc-123"})

        rate_logs = [log for log in captured if log.get("event") == "rate_limit_exceeded"]
        assert len(rate_logs) == 1
        assert rate_logs[0]["request_id"] == "req-abc-123"


class TestRateLimitLogSanitization:
    """429 logs must never contain sensitive data."""

    def test_sensitive_headers_not_logged(self):
        app, _limiter, captured = _build_test_app(limit_str="1/minute")
        client = TestClient(app)

        client.get(
            "/test-endpoint",
            headers={
                "Authorization": "Bearer secret-token",
                "X-Api-Key": "secret-key",
            },
        )
        client.get(
            "/test-endpoint",
            headers={
                "Authorization": "Bearer secret-token",
                "X-Api-Key": "secret-key",
            },
        )

        rate_logs = [log for log in captured if log.get("event") == "rate_limit_exceeded"]
        assert len(rate_logs) == 1
        log_str = json.dumps(rate_logs[0])

        assert "Bearer" not in log_str
        assert "secret-token" not in log_str
        assert "secret-key" not in log_str
        assert "password" not in log_str.lower()


class TestRateLimitEnvParser:
    """RATE_LIMIT_* environment variable parsing."""

    def _reset_env(self, keys):
        for key in keys:
            os.environ.pop(key, None)

    def test_valid_env_values(self, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_LOGIN", "10/minute")
        monkeypatch.setenv("RATE_LIMIT_UPLOAD", "20")
        monkeypatch.setenv("RATE_LIMIT_DEFAULT", "3")

        from app.rate_limiter import get_limit

        assert get_limit("RATE_LIMIT_LOGIN", "5/minute") == "10/minute"
        assert get_limit("RATE_LIMIT_UPLOAD", "10/minute") == "20/minute"
        assert get_limit("RATE_LIMIT_DEFAULT", "5/minute") == "3/minute"

    def test_missing_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.delenv("RATE_LIMIT_LOGIN", raising=False)

        from app.rate_limiter import get_limit

        assert get_limit("RATE_LIMIT_LOGIN", "5/minute") == "5/minute"

    def test_malformed_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_LOGIN", "not-a-valid-limit")

        from app.rate_limiter import get_limit

        assert get_limit("RATE_LIMIT_LOGIN", "5/minute") == "5/minute"

    def test_empty_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("RATE_LIMIT_LOGIN", "   ")

        from app.rate_limiter import get_limit

        assert get_limit("RATE_LIMIT_LOGIN", "5/minute") == "5/minute"
