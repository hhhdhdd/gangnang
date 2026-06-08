"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("user_id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column(
            "is_owner",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "receive_ideas",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "chats",
        sa.Column("chat_id", sa.BigInteger(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("schedule_cron", sa.String(length=64), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "ideas",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "chat_id",
            sa.BigInteger(),
            sa.ForeignKey("chats.chat_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("from_user_id", sa.BigInteger(), nullable=False),
        sa.Column("from_username", sa.String(length=64), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "is_anonymous",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'new'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ideas_chat_id", "ideas", ["chat_id"])
    op.create_index("ix_ideas_status", "ideas", ["status"])
    op.create_index("ix_ideas_created_at", "ideas", ["created_at"])

    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_index("ix_ideas_created_at", table_name="ideas")
    op.drop_index("ix_ideas_status", table_name="ideas")
    op.drop_index("ix_ideas_chat_id", table_name="ideas")
    op.drop_table("ideas")
    op.drop_table("chats")
    op.drop_table("admins")
