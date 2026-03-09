from typing import Annotated

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Verify API key from X-API-Key or Authorization: Bearer header."""
    api_key = get_settings().POLICY_SERVICE_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured",
        )

    provided = None
    if x_api_key:
        provided = x_api_key
    elif authorization and authorization.startswith("Bearer "):
        provided = authorization[7:]

    if not provided or provided != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
