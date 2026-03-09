from fastapi import FastAPI

from app.api.routes import policy

app = FastAPI(title="Policy Service", version="0.1.0")
app.include_router(policy.router)
