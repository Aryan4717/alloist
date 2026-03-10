import enum

from sqlalchemy import Column, Enum, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class OrgRole(str, enum.Enum):
    admin = "admin"
    developer = "developer"
    viewer = "viewer"


class OrganizationUser(Base):
    __tablename__ = "organization_users"
    __table_args__ = (PrimaryKeyConstraint("user_id", "org_id"),)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum(OrgRole), nullable=False)
