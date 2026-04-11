"""
tests/test_logger.py
Unit tests for core/logger.py — Structured Logging Layer (Sprint G-4).

Covers:
  - get_logger returns a logging.Logger
  - JSON formatter produces valid JSON
  - JSON entry has required fields: ts, level, logger, service, correlation_id, message
  - correlation_id_ctx is readable and settable
  - log_event emits without raising
  - log_event includes event field
  - GAIAEvent enum has expected values
  - PII guard: 'token', 'password', 'secret' fields are redacted
  - Text formatter produces non-JSON string
  - Multiple log_event calls with different GAIAEvents don't raise
"""
import json
import logging
import io
from core.logger import (
    GAIAEvent,
    _JSONFormatter,
    _TextFormatter,
    correlation_id_ctx,
    get_logger,
    log_event,
)


# ================================================================== #
#  get_logger                                                         #
# ================================================================== #

class TestGetLogger:
    def test_returns_logger_instance(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_named_correctly(self):
        logger = get_logger("test.named")
        assert logger.name == "test.named"

    def test_calling_twice_same_name_returns_same(self):
        a = get_logger("test.same")
        b = get_logger("test.same")
        assert a is b


# ================================================================== #
#  JSON Formatter                                                     #
# ================================================================== #

def _make_json_record(msg: str = "test message", **extra) -> str:
    formatter = _JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg=msg, args=(), exc_info=None,
    )
    for k, v in extra.items():
        setattr(record, k, v)
    return formatter.format(record)


class TestJSONFormatter:
    def test_produces_valid_json(self):
        output = _make_json_record()
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_has_required_fields(self):
        parsed = json.loads(_make_json_record())
        for field in ("ts", "level", "logger", "service", "correlation_id", "message"):
            assert field in parsed, f"Missing field: {field}"

    def test_level_is_INFO(self):
        parsed = json.loads(_make_json_record())
        assert parsed["level"] == "INFO"

    def test_message_correct(self):
        parsed = json.loads(_make_json_record("hello world"))
        assert parsed["message"] == "hello world"

    def test_extra_field_included(self):
        parsed = json.loads(_make_json_record(gaian="luna"))
        assert parsed["gaian"] == "luna"

    def test_event_field_included(self):
        parsed = json.loads(_make_json_record(event=GAIAEvent.GAIAN_BORN.value))
        assert parsed["event"] == "gaian.birth"

    def test_pii_token_redacted(self):
        parsed = json.loads(_make_json_record(token="supersecret"))
        assert parsed["token"] == "[REDACTED]"

    def test_pii_password_redacted(self):
        parsed = json.loads(_make_json_record(password="hunter2"))
        assert parsed["password"] == "[REDACTED]"

    def test_pii_secret_redacted(self):
        parsed = json.loads(_make_json_record(secret="mysecret"))
        assert parsed["secret"] == "[REDACTED]"

    def test_ts_is_iso8601(self):
        parsed = json.loads(_make_json_record())
        ts = parsed["ts"]
        assert ts.endswith("Z")
        assert "T" in ts


# ================================================================== #
#  Text Formatter                                                     #
# ================================================================== #

class TestTextFormatter:
    def test_produces_string(self):
        formatter = _TextFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        output = formatter.format(record)
        assert isinstance(output, str)

    def test_not_valid_json(self):
        formatter = _TextFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hello", args=(), exc_info=None,
        )
        output = formatter.format(record)
        try:
            json.loads(output)
            is_json = True
        except json.JSONDecodeError:
            is_json = False
        assert not is_json


# ================================================================== #
#  correlation_id_ctx                                                 #
# ================================================================== #

class TestCorrelationId:
    def test_default_is_dash(self):
        assert correlation_id_ctx.get("-") == "-"

    def test_settable(self):
        token = correlation_id_ctx.set("req-abc123")
        assert correlation_id_ctx.get("-") == "req-abc123"
        correlation_id_ctx.reset(token)

    def test_reset_restores_default(self):
        token = correlation_id_ctx.set("req-xyz")
        correlation_id_ctx.reset(token)
        assert correlation_id_ctx.get("-") == "-"


# ================================================================== #
#  log_event                                                          #
# ================================================================== #

class TestLogEvent:
    def test_does_not_raise(self):
        log_event(GAIAEvent.TURN_COMPLETE, message="test")

    def test_with_gaian_and_user(self):
        log_event(GAIAEvent.GAIAN_BORN, message="born", gaian="luna", user_id="u1")

    def test_all_event_types_do_not_raise(self):
        for event in GAIAEvent:
            log_event(event, message=f"test {event.value}")

    def test_extra_kwargs_accepted(self):
        log_event(GAIAEvent.ENGINE_CHAIN, message="chain",
                  bond_depth=0.42, synergy_factor=0.88, resonance_hz=528)


# ================================================================== #
#  GAIAEvent Enum                                                     #
# ================================================================== #

class TestGAIAEvent:
    def test_gaian_born_value(self):
        assert GAIAEvent.GAIAN_BORN == "gaian.birth"

    def test_turn_complete_value(self):
        assert GAIAEvent.TURN_COMPLETE == "turn.complete"

    def test_error_value(self):
        assert GAIAEvent.ERROR == "error"

    def test_request_in_value(self):
        assert GAIAEvent.REQUEST_IN == "http.request"

    def test_all_values_are_strings(self):
        for event in GAIAEvent:
            assert isinstance(event.value, str)

    def test_all_values_are_dot_namespaced(self):
        for event in GAIAEvent:
            assert "." in event.value, f"{event} value is not dot-namespaced: {event.value}"
