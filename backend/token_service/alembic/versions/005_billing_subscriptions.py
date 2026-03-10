"""billing_subscriptions

Revision ID: 005
Revises: 004
Create Date: 2026-03-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, Sequence[str], None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_subscriptions_org_id",
        "subscriptions",
        ["org_id"],
        unique=True,
    )

    op.create_table(
        "org_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("enforcement_checks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("policy_evaluations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_org_usage_org_id_period_start",
        "org_usage",
        ["org_id", "period_start"],
        unique=True,
    )

    op.execute(f"""
    INSERT INTO subscriptions (id, org_id, plan, status, created_at, updated_at)
    VALUES (gen_random_uuid(), '{DEFAULT_ORG_ID}'::uuid, 'free', 'active', NOW(), NOW())
    ON CONFLICT (org_id) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index("ix_org_usage_org_id_period_start", table_name="org_usage")
    op.drop_table("org_usage")
    op.drop_index("ix_subscriptions_org_id", table_name="subscriptions")
    op.drop_table("subscriptions")
