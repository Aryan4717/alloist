"""multi_tenant

Revision ID: 002
Revises: 001
Create Date: 2026-03-09

"""
from typing import Sequence, Union

import hashlib

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000002"
DEFAULT_API_KEY = "dev-api-key"


def upgrade() -> None:
    # Create orgrole enum
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE orgrole AS ENUM ('admin', 'developer', 'viewer');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    """)

    orgrole_enum = postgresql.ENUM("admin", "developer", "viewer", name="orgrole", create_type=False)

    # Create organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # Create users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Create organization_users
    op.create_table(
        "organization_users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", orgrole_enum, nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "org_id"),
    )

    # Create api_keys
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("key_prefix", sa.String(8), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])

    # Add org_id to tokens (nullable first)
    op.add_column("tokens", sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True))

    # Seed default org, user, org_user
    op.execute(f"""
    INSERT INTO organizations (id, name, created_at)
    VALUES ('{DEFAULT_ORG_ID}', 'Default', NOW())
    ON CONFLICT (id) DO NOTHING
    """)
    op.execute(f"""
    INSERT INTO users (id, email, name)
    VALUES ('{DEFAULT_USER_ID}', 'admin@alloist.local', 'Admin')
    ON CONFLICT (id) DO NOTHING
    """)
    op.execute(f"""
    INSERT INTO organization_users (user_id, org_id, role)
    VALUES ('{DEFAULT_USER_ID}', '{DEFAULT_ORG_ID}', 'admin')
    ON CONFLICT (user_id, org_id) DO NOTHING
    """)

    # Seed API key for dev-api-key
    key_hash = hashlib.sha256(DEFAULT_API_KEY.encode()).hexdigest()
    key_prefix = DEFAULT_API_KEY[:8] if len(DEFAULT_API_KEY) >= 8 else DEFAULT_API_KEY.ljust(8, "x")
    op.execute(f"""
    INSERT INTO api_keys (id, user_id, key_hash, key_prefix, created_at)
    SELECT gen_random_uuid(), '{DEFAULT_USER_ID}', '{key_hash}', '{key_prefix}', NOW()
    WHERE NOT EXISTS (SELECT 1 FROM api_keys WHERE key_prefix = '{key_prefix}')
    """)

    # Backfill existing tokens with default org
    op.execute(f"UPDATE tokens SET org_id = '{DEFAULT_ORG_ID}' WHERE org_id IS NULL")

    # Make org_id NOT NULL
    op.alter_column(
        "tokens",
        "org_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_tokens_org_id",
        "tokens",
        "organizations",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tokens_org_id", "tokens", type_="foreignkey")
    op.drop_column("tokens", "org_id")
    op.drop_table("api_keys")
    op.drop_table("organization_users")
    op.drop_table("users")
    op.drop_table("organizations")
    postgresql.ENUM("admin", "developer", "viewer", name="orgrole").drop(op.get_bind(), checkfirst=True)
