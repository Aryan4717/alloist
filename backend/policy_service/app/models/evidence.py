import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    action_name = Column(String(255), nullable=False)
    token_snapshot = Column(JSONB, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    input_hash = Column(String(64), nullable=False)
    policy_id = Column(UUID(as_uuid=True), nullable=True)
    result = Column(String(10), nullable=False)  # "allow" or "deny"
    runtime_signature = Column(Text, nullable=False)
    runtime_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
