import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    retention_days = Column(Integer, nullable=True, default=30)
    allowed_domain = Column(String(255), nullable=True)  # e.g. "acme.com" for org email matching
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
