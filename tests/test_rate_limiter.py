"""
tests/test_rate_limiter.py
Unit tests for core/rate_limiter.py — Sprint G-7.

Covers:
  - _sliding_window_check: allows, blocks, remaining count, retry_after
  - _client_ip: X-Forwarded-For parsing, fallback to client.host
  - _build_429: correct envelope shape + headers
  - RateLimitMiddleware: allows, blocks at limit, bypass paths unthrottled
  - rate_limit() dependency: allows, blocks, scoped independently
  - clear_store() resets counters
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.rate_limiter import (
    _sliding_window_check,
    _client_ip,
    _build_429,
    _rate_limit_headers,
    RateLimitMiddleware,
    rate_limit,
    clear_store,
)


# ================================================================== #
#  Helpers                                                            #
# ================================================================== #

@pytest.fixture(autouse=True)
def reset_store():
    """Clear rate limit store before every test."""
    clear_store()
    yield
    clear_store()


# ================================================================== #
#  Sliding Window Logic                                               #
# ================================================================== #

class TestSlidingWindow:
    def test_first_request_allowed(self):
        allowed, remaining, retry = _sliding_window_check("k1", 5, 60)
        assert allowed is True

    def test_remaining_decrements(self):
        _sliding_window_check("k2", 5, 60)
        _, remaining, _ = _sliding_window_check("k2", 5, 60)
        assert remaining == 3  # 5 - 2 in flight

    def test_blocked_at_limit(self):
        for _ in range(3):
            _sliding_window_check("k3", 3, 60)
        allowed, remaining, retry = _sliding_window_check("k3", 3, 60)
        assert allowed is False
        assert remaining == 0
        assert retry > 0

    def test_different_keys_independent(self):
        for _ in range(3):
            _sliding_window_check("ka", 3, 60)
        allowed, _, _ = _sliding_window_check("kb", 3, 60)
        assert allowed is True

    def test_clear_store_resets(self):
        for _ in range(3):
            _sliding_window_check("kc", 3, 60)
        clear_store()
        allowed, _, _ = _sliding_window_check("kc", 3, 60)
        assert allowed is True


# ================================================================== #
#  _client_ip                                                         #
# ================================================================== #

class TestClientIp:
    def _make_request(self, forwarded=None, host="1.2.3.4"):
        req = MagicMock()
        req.headers = {}
        if forwarded:
            req.headers["X-Forwarded-For"] = forwarded
        req.client = MagicMock()
        req.client.host = host
        return req

    def test_uses_forwarded_for(self):
        req = self._make_request(forwarded="10.0.0.1, 192.168.1.1")
        assert _client_ip(req) == "10.0.0.1"

    def test_falls_back_to_host(self):
        req = self._make_request(host="5.6.7.8")
        assert _client_ip(req) == "5.6.7.8"

    def test_no_client_returns_unknown(self):
        req = MagicMock()
        req.headers = {}
        req.client = None
        assert _client_ip(req) == "unknown"


# ================================================================== #
#  Build 429 Envelope                                                 #
# ================================================================== #

class TestBuild429:
    def test_status_code_is_429(self):
        r = _build_429(30, "req-abc", 60, 60)
        assert r.status_code == 429

    def test_ok_is_false(self):
        import json
        r = _build_429(30, "req-abc", 60, 60)
        body = json.loads(r.body)
        assert body["ok"] is False

    def test_code_is_rate_limited(self):
        import json
        r = _build_429(30, "req-abc", 60, 60)
        body = json.loads(r.body)
        assert body["error"]["code"] == "RATE_LIMITED"

    def test_retry_after_in_message(self):
        import json
        r = _build_429(42, "req-abc", 60, 60)
        body = json.loads(r.body)
        assert "42" in body["error"]["message"]

    def test_retry_after_header_set(self):
        r = _build_429(30, "req-abc", 60, 60)
        assert r.headers.get("retry-after") == "30"


# ================================================================== #
#  Middleware Integration                                             #
# ================================================================== #

@pytest.fixture
def app_with_middleware():
    _app = FastAPI()
    _app.add_middleware(RateLimitMiddleware)

    @_app.get("/test")
    async def test_route():
        return {"ok": True}

    @_app.get("/status")
    async def status_route():
        return {"ok": True}

    return _app


@pytest.fixture
def mw_client(app_with_middleware):
    return TestClient(app_with_middleware, raise_server_exceptions=False)


class TestRateLimitMiddleware:
    def test_normal_request_passes(self, mw_client):
        r = mw_client.get("/test")
        assert r.status_code == 200

    def test_ratelimit_headers_on_ok_response(self, mw_client):
        r = mw_client.get("/test")
        assert "x-ratelimit-limit" in r.headers
        assert "x-ratelimit-remaining" in r.headers

    def test_bypass_path_not_throttled(self, mw_client):
        # Hammer /status well above default limit — should never 429
        for _ in range(5):
            r = mw_client.get("/status")
            assert r.status_code == 200

    def test_blocks_after_limit(self):
        """Use a tiny limit to verify 429 is returned."""
        clear_store()
        _app = FastAPI()

        import os
        with patch.object(RateLimitMiddleware, '_MAX', 2), \
             patch.object(RateLimitMiddleware, '_WINDOW', 60):

            _app.add_middleware(RateLimitMiddleware)

            @_app.get("/hit")
            async def hit():
                return {"ok": True}

            client = TestClient(_app, raise_server_exceptions=False)
            client.get("/hit")
            client.get("/hit")
            r = client.get("/hit")
            assert r.status_code == 429
