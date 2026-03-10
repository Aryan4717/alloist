"""FastAPI middleware for request/response logging with request_id."""

import time
from contextvars import ContextVar
from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Get the current request_id from context."""
    return _request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """Set the request_id in context."""
    _request_id_ctx.set(request_id)


def clear_request_id() -> None:
    """Clear the request_id from context."""
    try:
        _request_id_ctx.set(None)
    except LookupError:
        pass


def logging_middleware(service_name: str):
    """Create FastAPI middleware that logs requests and responses with request_id."""

    class LoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request_id = str(uuid4())
            request.state.request_id = request_id
            set_request_id(request_id)

            start = time.perf_counter()
            logger = structlog.get_logger().bind(service=service_name, request_id=request_id)

            try:
                logger.info(
                    "request_started",
                    method=request.method,
                    path=request.url.path,
                )
                response = await call_next(request)
                latency_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    "request_completed",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    latency_ms=round(latency_ms, 2),
                )
                return response
            except Exception as exc:
                latency_ms = (time.perf_counter() - start) * 1000
                logger.exception(
                    "request_failed",
                    method=request.method,
                    path=request.url.path,
                    latency_ms=round(latency_ms, 2),
                    error=str(exc),
                )
                raise
            finally:
                clear_request_id()

    return LoggingMiddleware
