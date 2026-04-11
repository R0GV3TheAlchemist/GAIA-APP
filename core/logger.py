"""
core/logger.py
GAIA Structured Logging Layer — Sprint G-4

Provides:
  - get_logger(name)        — returns a named logger emitting structured JSON lines
  - log_event(...)          — typed event helper; emits a single structured log entry
  - GAIAEvent               — enum of all canonical event types
  - correlation_id_ctx      — ContextVar for per-request correlation ID
  - LoggingMiddleware       — FastAPI middleware: stamps every request with a
                              correlation ID and logs request + response

Log format (one JSON object per line, stdout):
  {
    "ts":             "2026-04-11T20:00:00.000Z",   ISO-8601 UTC
    "level":          "INFO",
    "logger":         "core.server",
    "event":          "gaian.birth",                 GAIAEvent value
    "correlation_id": "req-abc123",                  per-request UUID prefix
    "gaian":          "luna",                        optional, present when relevant
    "user_id":        "u-xyz",                       optional
    "message":        "Human-readable summary",
    ...extra                                          any extra key=value fields
  }

In development (GAIA_LOG_FORMAT=text), emits coloured human-readable lines instead.
Default is JSON. Set GAIA_LOG_FORMAT=text in your .env for local dev readability.

Canon Ref: C01 (Sovereignty — audit trail), C15 (Consent — no PII in logs)

Usage:
    from core.logger import get_logger, log_event, GAIAEvent

    logger = get_logger(__name__)
    logger.info("Engine chain complete", extra={"event": GAIAEvent.TURN_COMPLETE.value})

    # Or use the helper:
    log_event(GAIAEvent.GAIAN_BORN, gaian="luna", user_id="u1", zodiac="scorpio")
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# ------------------------------------------------------------------ #
#  Config                                                              #
# ------------------------------------------------------------------ #

_LOG_FORMAT  = os.environ.get("GAIA_LOG_FORMAT", "json").lower()   # "json" | "text"
_LOG_LEVEL   = os.environ.get("GAIA_LOG_LEVEL",  "INFO").upper()
_SERVICE     = os.environ.get("GAIA_SERVICE_NAME", "gaia-api")

# Per-request correlation ID — set by LoggingMiddleware, read by log_event
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


# ------------------------------------------------------------------ #
#  Canonical Event Types                                              #
# ------------------------------------------------------------------ #

class GAIAEvent(str, Enum):
    # Lifecycle
    SERVER_START        = "server.start"
    SERVER_READY        = "server.ready"

    # HTTP
    REQUEST_IN          = "http.request"
    RESPONSE_OUT        = "http.response"

    # Auth
    TOKEN_ISSUED        = "auth.token.issued"
    TOKEN_VERIFIED      = "auth.token.verified"
    AUTH_FAILED         = "auth.failed"
    ADMIN_ACCESS        = "auth.admin.access"

    # GAIAN
    GAIAN_BORN          = "gaian.birth"
    GAIAN_LOADED        = "gaian.loaded"
    GAIAN_RUNTIME_INIT  = "gaian.runtime.init"

    # Conversation
    TURN_START          = "turn.start"
    TURN_COMPLETE       = "turn.complete"
    TURN_ERROR          = "turn.error"

    # Engine chain
    ENGINE_CHAIN        = "engine.chain"
    SOUL_MIRROR_NUDGE   = "engine.soul_mirror.nudge"
    RESONANCE_PEAK      = "engine.resonance.peak"
    SYNERGY_HIGH        = "engine.synergy.high"
    SCHUMANN_ALIGNED    = "engine.schumann.aligned"

    # Memory
    MEMORY_SAVED        = "memory.saved"
    MEMORY_LOADED       = "memory.loaded"

    # Canon
    CANON_LOADED        = "canon.loaded"
    CANON_SEARCH        = "canon.search"

    # Errors
    ERROR               = "error"
    UNHANDLED_EXCEPTION = "error.unhandled"


# ------------------------------------------------------------------ #
#  Structured JSON Formatter                                          #
# ------------------------------------------------------------------ #

class _JSONFormatter(logging.Formatter):
    """
    Formats each log record as a single JSON object on one line.
    Merges the record's `extra` dict into the top-level JSON object.
    PII guard: strips any field named 'password', 'token', 'secret'.
    """
    _REDACT = frozenset({"password", "token", "secret", "api_key", "admin_key"})

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts":             datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level":          record.levelname,
            "logger":         record.name,
            "service":        _SERVICE,
            "correlation_id": correlation_id_ctx.get("-"),
            "message":        record.getMessage(),
        }
        # Merge any extra fields passed via extra={...}
        for key, val in record.__dict__.items():
            if key in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            ):
                continue
            if key.startswith("_"):
                continue
            if key in self._REDACT:
                entry[key] = "[REDACTED]"
            else:
                entry[key] = val

        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str, ensure_ascii=False)


# ------------------------------------------------------------------ #
#  Human-Readable Text Formatter (dev mode)                          #
# ------------------------------------------------------------------ #

_COLOURS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}
_RESET = "\033[0m"


class _TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        ts     = datetime.now(timezone.utc).strftime("%H:%M:%S")
        cid    = correlation_id_ctx.get("-")[:8]
        event  = getattr(record, "event", "")
        event_str = f" [{event}]" if event else ""
        gaian  = getattr(record, "gaian", "")
        gaian_str = f" gaian={gaian}" if gaian else ""
        base = f"{colour}{ts} {record.levelname:<8}{_RESET} [{cid}] {record.name}{event_str}{gaian_str}: {record.getMessage()}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


# ------------------------------------------------------------------ #
#  Logger Factory                                                     #
# ------------------------------------------------------------------ #

_configured = False


def _configure_root() -> None:
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger()
    root.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))

    # Remove any handlers added by basicConfig
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _TextFormatter() if _LOG_FORMAT == "text" else _JSONFormatter()
    )
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "watchfiles", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger using the GAIA structured format.
    Call once at module level: logger = get_logger(__name__)
    """
    _configure_root()
    return logging.getLogger(name)


# ------------------------------------------------------------------ #
#  Typed Event Helper                                                 #
# ------------------------------------------------------------------ #

_event_logger = None


def log_event(
    event:          GAIAEvent,
    level:          int          = logging.INFO,
    message:        str          = "",
    gaian:          Optional[str] = None,
    user_id:        Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Emit a single structured log entry for a canonical GAIA event.

    Args:
        event:    GAIAEvent enum value (e.g. GAIAEvent.GAIAN_BORN)
        level:    logging level (default INFO)
        message:  human-readable summary
        gaian:    GAIAN slug (optional)
        user_id:  authenticated user ID (optional)
        **kwargs: any extra fields to include in the log entry
    """
    global _event_logger
    if _event_logger is None:
        _event_logger = get_logger("gaia.events")

    extra: dict[str, Any] = {"event": event.value}
    if gaian:
        extra["gaian"] = gaian
    if user_id:
        extra["user_id"] = user_id
    extra.update(kwargs)

    _event_logger.log(level, message or event.value, extra=extra)


# ------------------------------------------------------------------ #
#  FastAPI Logging Middleware                                         #
# ------------------------------------------------------------------ #

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Stamps every incoming request with a correlation ID.
    Logs: method, path, status_code, duration_ms.
    The correlation ID is available via correlation_id_ctx throughout
    the entire async call chain for that request.
    """

    def __init__(self, app, service_name: str = _SERVICE):
        super().__init__(app)
        self._service = service_name
        self._logger  = get_logger("gaia.http")

    async def dispatch(self, request: Request, call_next) -> Response:
        cid   = "req-" + uuid.uuid4().hex[:12]
        token = correlation_id_ctx.set(cid)

        import time
        t0 = time.perf_counter()

        self._logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "event":  GAIAEvent.REQUEST_IN.value,
                "method": request.method,
                "path":   request.url.path,
                "query":  str(request.url.query) or None,
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            self._logger.error(
                f"Unhandled exception: {exc}",
                exc_info=True,
                extra={"event": GAIAEvent.UNHANDLED_EXCEPTION.value},
            )
            raise
        finally:
            correlation_id_ctx.reset(token)

        duration_ms = round((time.perf_counter() - t0) * 1000, 1)

        self._logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)",
            extra={
                "event":       GAIAEvent.RESPONSE_OUT.value,
                "method":      request.method,
                "path":        request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Return correlation ID to client for debugging
        response.headers["X-Correlation-ID"] = cid
        return response
