"""add_dsl_to_policies

Revision ID: 003
Revises: 002
Create Date: 2025-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "policies",
        sa.Column("dsl", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("policies", "dsl")
