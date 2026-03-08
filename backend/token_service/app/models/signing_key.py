from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.database import Base


class SigningKey(Base):
    __tablename__ = "signing_keys"

    id = Column(String(64), primary_key=True)
    algorithm = Column(String(32), nullable=False, default="Ed25519")
    private_key = Column(Text, nullable=False)
    public_key = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=False)
