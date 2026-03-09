"""create_evidence

Revision ID: 002
Revises: 001
Create Date: 2025-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action_name", sa.String(255), nullable=False),
        sa.Column("token_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("result", sa.String(10), nullable=False),
        sa.Column("runtime_signature", sa.Text(), nullable=False),
        sa.Column("runtime_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evidence")
