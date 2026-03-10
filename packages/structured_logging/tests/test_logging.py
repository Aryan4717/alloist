"""Tests for alloist_logging."""

from alloist_logging import get_logger, log_event
from alloist_logging.middleware import clear_request_id, get_request_id, set_request_id


def test_get_logger_returns_logger():
    """get_logger returns a structlog logger with service bound."""
    logger = get_logger("test_service")
    assert logger is not None
    logger.info("test_event", key="value")  # No exception


def test_log_event_no_exception():
    """log_event runs without exception."""
    set_request_id("test-request-123")
    logger = get_logger("test_service")
    log_event(
        logger,
        action="test_action",
        result="success",
        org_id="org-1",
        user_id="user-1",
        latency_ms=42.5,
    )
    clear_request_id()


def test_request_id_context():
    """request_id context var works correctly."""
    clear_request_id()
    assert get_request_id() in (None, "")

    set_request_id("req-abc")
    assert get_request_id() == "req-abc"

    clear_request_id()
    rid = get_request_id()
    assert rid in (None, "")
