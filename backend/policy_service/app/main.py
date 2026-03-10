import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import text

from alloist_logging import logging_middleware
from alloist_metrics import get_metrics_output, health_router, metrics_middleware

from app.api.routes import audit, consent, evidence, policy
from app.config import get_settings
from app.database import SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def cleanup_loop():
        from app.services.audit_service import delete_expired_logs

        while True:
            await asyncio.sleep(get_settings().AUDIT_CLEANUP_INTERVAL_SEC)
            db = SessionLocal()
            try:
                delete_expired_logs(db)
            finally:
                db.close()

    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Policy Service", version="0.1.0", lifespan=lifespan)
app.add_middleware(logging_middleware("policy_service"))
app.add_middleware(metrics_middleware("policy_service"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "null",  # Extension popup may send null origin
    ],
    allow_origin_regex=r"chrome-extension://.*",  # Allow Chrome extension WebSocket connections
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@app.get("/metrics")
def metrics():
    return Response(content=get_metrics_output(), media_type="text/plain; version=0.0.4")


app.include_router(health_router(check_ready=_check_ready))
app.include_router(policy.router)
app.include_router(consent.router)
app.include_router(evidence.router)
app.include_router(audit.router)
