from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: UUID
    org_id: UUID
    action: str
    result: str
    metadata: dict[str, Any] | None = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogItem]
    total: int
