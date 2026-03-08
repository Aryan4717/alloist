from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MintTokenRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    ttl_seconds: int = Field(..., gt=0, le=86400 * 365)  # max 1 year


class MintTokenResponse(BaseModel):
    token: str
    token_id: UUID
    expires_at: datetime


class RevokeTokenRequest(BaseModel):
    token_id: UUID


class ValidateTokenRequest(BaseModel):
    token: str


class ValidateTokenResponse(BaseModel):
    valid: bool
    status: str  # "active" | "revoked"
    subject: str
    scopes: list[str]
    jti: str


class RevokeTokenResponse(BaseModel):
    success: bool = True


class TokenMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject: str
    scopes: list[str]
    issued_at: datetime
    expires_at: datetime
    status: str
