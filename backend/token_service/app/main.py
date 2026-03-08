from fastapi import FastAPI

from app.api.routes import keys, tokens, websocket

app = FastAPI(title="Token Service", version="0.1.0")
app.include_router(tokens.router)
app.include_router(keys.router)
app.include_router(websocket.router)
