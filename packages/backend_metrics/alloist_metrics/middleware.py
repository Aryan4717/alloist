"""FastAPI/Starlette middleware for HTTP request latency metrics."""

import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from alloist_metrics.prometheus import create_metrics

# Path normalization: replace UUIDs with {id} to limit cardinality
UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def _normalize_path(path: str) -> str:
    """Replace UUIDs in path with {id} for lower cardinality."""
    return UUID_PATTERN.sub("{id}", path)


def metrics_middleware(service_name: str):
    """Create middleware that records HTTP request duration in http_request_duration_ms histogram."""

    metrics = create_metrics(service_name)

    class MetricsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start = time.perf_counter()
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            path = _normalize_path(request.url.path)
            metrics.observe_http_request(
                method=request.method,
                path=path,
                status=response.status_code,
                duration_ms=duration_ms,
            )
            return response

    return MetricsMiddleware
