from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TokenSnapshotSchema(BaseModel):
    kid: str = Field(..., min_length=1)
    token_id: str = Field(..., min_length=1)
    scopes: list[str] = Field(default_factory=list)


class CreateEvidenceRequest(BaseModel):
    evidence_id: UUID
    action_name: str = Field(..., min_length=1, max_length=255)
    token_snapshot: dict[str, Any] = Field(...)  # { kid, token_id, scopes }
    policy_id: UUID | None = None
    result: str = Field(..., pattern="^(allow|deny)$")
    runtime_metadata: dict[str, Any] = Field(default_factory=dict)


class CreateEvidenceResponse(BaseModel):
    evidence_id: UUID


class ExportEvidenceRequest(BaseModel):
    evidence_id: UUID


class ExportEvidenceResponse(BaseModel):
    bundle: dict[str, Any]
    signature: str
    public_key: str


class EvidenceKeysResponse(BaseModel):
    public_key: str


class EvidenceListItem(BaseModel):
    id: UUID
    action_name: str
    result: str
    timestamp: datetime
    policy_id: UUID | None
    token_snapshot: dict[str, Any]


class EvidenceListResponse(BaseModel):
    items: list[EvidenceListItem]
    total: int
