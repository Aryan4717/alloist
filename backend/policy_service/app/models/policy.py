import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rules = Column(JSONB, nullable=False)
    dsl = Column(JSONB, nullable=True)  # Original DSL for UI rehydration
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
