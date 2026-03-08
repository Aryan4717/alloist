from fastapi import FastAPI

from app.api.routes import tokens

app = FastAPI(title="Token Service", version="0.1.0")
app.include_router(tokens.router)
