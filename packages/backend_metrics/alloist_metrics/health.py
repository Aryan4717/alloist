"""Health and readiness endpoints."""

from typing import Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse


def health_router(
    check_ready: Callable[[], bool] | None = None,
) -> APIRouter:
    """
    Create router with GET /health (liveness) and GET /ready (readiness).
    check_ready: optional callable that returns True if service is ready (e.g. DB ping).
    """
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health():
        """Liveness probe - always returns 200 if process is up."""
        return JSONResponse(content={"status": "ok"})

    @router.get("/ready")
    def ready():
        """Readiness probe - returns 200 if dependencies (DB, etc.) are available."""
        if check_ready is None:
            return JSONResponse(content={"status": "ok"})
        if check_ready():
            return JSONResponse(content={"status": "ok"})
        return JSONResponse(
            content={"status": "unhealthy"},
            status_code=503,
        )

    return router
