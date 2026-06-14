"""suno_keys — multiple Suno API keys with rotation

Revision ID: 0010_suno_keys
Revises: 0009_daily_songs
Create Date: 2026-06-14

Adds the ``suno_keys`` table so the bot can hold several sunoapi.org
API keys and rotate between them when free credits run low. One key is
``is_active`` at a time; the credit-refresh scheduler job updates
``last_credits`` and rotates to the next enabled key when the active
one drops below the threshold.

The legacy single key (``settings['suno.api_key']``) is migrated into
this table on first read (see ``app/services/suno.py``); no data is
lost — this migration only creates the table.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_suno_keys"
down_revision: Union[str, None] = "0009_daily_songs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suno_keys",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True,
            nullable=False,
        ),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("last_credits", sa.Integer(), nullable=True),
        sa.Column(
            "last_checked_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("api_key", name="uq_suno_keys_api_key"),
    )


def downgrade() -> None:
    op.drop_table("suno_keys")
