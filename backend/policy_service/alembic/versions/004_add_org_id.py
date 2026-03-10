"""add_org_id

Revision ID: 004
Revises: 003
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, Sequence[str], None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.add_column(
        "policies",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "evidence",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(f"UPDATE policies SET org_id = '{DEFAULT_ORG_ID}' WHERE org_id IS NULL")
    op.execute(f"UPDATE evidence SET org_id = '{DEFAULT_ORG_ID}' WHERE org_id IS NULL")
    op.alter_column(
        "policies",
        "org_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.alter_column(
        "evidence",
        "org_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_policies_org_id",
        "policies",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_evidence_org_id",
        "evidence",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_policies_org_id", "policies", type_="foreignkey")
    op.drop_constraint("fk_evidence_org_id", "evidence", type_="foreignkey")
    op.drop_column("policies", "org_id")
    op.drop_column("evidence", "org_id")
