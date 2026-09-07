import os
import sys
import logging
import re

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

_RATE_LIMIT_PATTERN = re.compile(r"^\d+(/[a-z]+)?$", re.IGNORECASE)


def _env_limit(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    value = value.strip()
    if "/" not in value:
        value = f"{value}/minute"
    if not _RATE_LIMIT_PATTERN.match(value):
        logger.warning(
            "Invalid rate limit format for %s=%r; falling back to default %r",
            name,
            os.getenv(name),
            default,
        )
        return default
    return value


_RATE_LIMIT_STORAGE = os.getenv("RATE_LIMIT_STORAGE", "memory://")
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_RATE_LIMIT_STORAGE,
    default_limits=[_env_limit("RATE_LIMIT_DEFAULT", "5/minute")],
)


def get_limit(env_name: str, default: str) -> str:
    """Return a rate-limit string from an environment variable, falling back to default."""
    return _env_limit(env_name, default)


def get_rate_limit_storage_description() -> str:
    """Return a safe description of the configured rate-limit storage for logging."""
    storage = os.getenv("RATE_LIMIT_STORAGE", "memory://")
    if storage.startswith("memory://"):
        return "in-memory (single-worker only)"
    if storage.startswith("redis://"):
        return "shared Redis"
    return "configured storage backend"


def _detect_worker_count() -> int:
    """Return the number of worker processes from env vars or CLI args."""
    for env_var in ("WEB_CONCURRENCY", "WORKERS"):
        value = os.getenv(env_var)
        if value and value.strip().isdigit():
            return int(value.strip())

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("--workers", "-w") and i + 1 < len(args):
            try:
                return int(args[i + 1])
            except ValueError:
                pass
        if arg.startswith("--workers="):
            try:
                return int(arg.split("=", 1)[1])
            except ValueError:
                pass

    return 1


def _check_rate_limit_storage_on_startup():
    """Fail fast in production if memory:// storage is used with multiple workers."""
    storage = os.getenv("RATE_LIMIT_STORAGE", "memory://")
    if not storage.startswith("memory://"):
        return

    workers = _detect_worker_count()
    if workers <= 1:
        return

    environment = os.getenv("ENVIRONMENT", "development")
    message = (
        "Rate limiting storage is memory://, which is process-local and not shared "
        f"across {workers} workers. Set RATE_LIMIT_STORAGE to a shared backend "
        "(e.g., redis://redis:6379) before scaling beyond one worker."
    )

    if environment == "production":
        raise RuntimeError(message)
    logger.warning(message)
