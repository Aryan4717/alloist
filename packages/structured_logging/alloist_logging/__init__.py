"""Structured JSON logging for Alloist backend services."""

from alloist_logging.config import configure_structlog
from alloist_logging.middleware import (
    clear_request_id,
    get_request_id,
    logging_middleware,
    set_request_id,
)

# Configure on import so services get JSON output immediately
configure_structlog()


def get_logger(service_name: str):
    """Return a structlog logger bound with the service name."""
    import structlog

    return structlog.get_logger().bind(service=service_name)


def log_event(
    logger,
    action: str,
    result: str,
    org_id: str | None = None,
    user_id: str | None = None,
    latency_ms: float | None = None,
    **extra,
) -> None:
    """Log a critical event with required fields. Reads request_id from context."""
    from alloist_logging.middleware import get_request_id

    request_id = get_request_id()
    payload = {
        "action": action,
        "result": result,
        "request_id": request_id,
        "org_id": str(org_id) if org_id is not None else None,
        "user_id": str(user_id) if user_id is not None else None,
        "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
        **extra,
    }
    # Remove None values for cleaner JSON
    payload = {k: v for k, v in payload.items() if v is not None}
    logger.info(action, **payload)


__all__ = [
    "get_logger",
    "log_event",
    "logging_middleware",
    "configure_structlog",
    "get_request_id",
    "set_request_id",
    "clear_request_id",
]
