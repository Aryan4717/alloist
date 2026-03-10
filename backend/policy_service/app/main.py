import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audit, evidence, policy
from app.config import get_settings
from app.database import SessionLocal


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(policy.router)
app.include_router(evidence.router)
app.include_router(audit.router)
