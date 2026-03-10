from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import text

from alloist_logging import logging_middleware
from alloist_metrics import get_metrics_output, health_router, metrics_middleware

from app.api.routes import auth, billing, keys, tokens, websocket
from app.database import engine

app = FastAPI(title="Token Service", version="0.1.0")
app.add_middleware(logging_middleware("token_service"))
app.add_middleware(metrics_middleware("token_service"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
app.include_router(tokens.router)
app.include_router(billing.router)
app.include_router(keys.router)
app.include_router(websocket.router)
app.include_router(auth.router)
