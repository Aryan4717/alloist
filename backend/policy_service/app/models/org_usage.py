import uuid
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class OrgUsage(Base):
    __tablename__ = "org_usage"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(Date, nullable=False)
    enforcement_checks = Column(Integer, nullable=False, default=0)
    tokens_created = Column(Integer, nullable=False, default=0)
    policy_evaluations = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
