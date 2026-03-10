import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class TokenStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"


class Token(Base):
    __tablename__ = "tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(255), nullable=False)
    scopes = Column(JSONB, nullable=False, default=list)
    issued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    status = Column(Enum(TokenStatus), nullable=False, default=TokenStatus.active)
    signing_key_id = Column(String(64), nullable=False)
    token_value = Column(Text, nullable=False)
