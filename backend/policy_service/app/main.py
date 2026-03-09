from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import evidence, policy

app = FastAPI(title="Policy Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(policy.router)
app.include_router(evidence.router)
