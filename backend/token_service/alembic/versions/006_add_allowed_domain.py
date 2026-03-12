"""add_allowed_domain

Revision ID: 006
Revises: 005
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, Sequence[str], None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("allowed_domain", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("organizations", "allowed_domain")
