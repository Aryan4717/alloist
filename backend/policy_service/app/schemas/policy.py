from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActionSchema(BaseModel):
    service: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluateRequest(BaseModel):
    token_id: UUID
    action: ActionSchema


class EvaluateResponse(BaseModel):
    allowed: bool
    policy_id: UUID | None = None
    reason: str | None = None


class CreatePolicyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    rules: dict[str, Any] = Field(...)


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    rules: dict[str, Any]
    created_at: datetime
