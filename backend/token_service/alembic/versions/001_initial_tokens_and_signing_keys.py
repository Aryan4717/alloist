"""initial_tokens_and_signing_keys

Revision ID: 001
Revises:
Create Date: 2025-03-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum explicitly; use postgresql.ENUM with create_type=False for column to avoid duplicate creation
    token_status_enum = postgresql.ENUM("active", "revoked", name="tokenstatus")
    token_status_enum.create(op.get_bind(), checkfirst=True)

    token_status_enum_col = postgresql.ENUM("active", "revoked", name="tokenstatus", create_type=False)

    op.create_table(
        "signing_keys",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("algorithm", sa.String(32), nullable=False),
        sa.Column("private_key", sa.Text(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("status", token_status_enum_col, nullable=False),
        sa.Column("signing_key_id", sa.String(64), nullable=False),
        sa.Column("token_value", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("tokens")
    op.drop_table("signing_keys")
    postgresql.ENUM("active", "revoked", name="tokenstatus").drop(op.get_bind(), checkfirst=True)
