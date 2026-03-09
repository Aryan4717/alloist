"""Minimal Token model for read-only access to tokens table (shared DB with token_service)."""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class TokenStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"


class TokenRef(Base):
    """Read-only reference to tokens table for policy evaluation."""

    __tablename__ = "tokens"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True)
    subject = Column(String(255), nullable=False)
    scopes = Column(JSONB, nullable=False, default=list)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(Enum(TokenStatus), nullable=False)
    signing_key_id = Column(String(64), nullable=False)
    token_value = Column(Text, nullable=False)
