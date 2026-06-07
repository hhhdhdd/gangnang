"""voting on ideas

Revision ID: 0005_voting
Revises: 0004_admins_delivery
Create Date: 2026-06-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_voting"
down_revision: Union[str, None] = "0004_admins_delivery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column(
            "auto_publish",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "ideas",
        sa.Column("published_chat_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "ideas",
        sa.Column("published_message_id", sa.BigInteger(), nullable=True),
    )

    op.create_table(
        "idea_votes",
        sa.Column(
            "idea_id",
            sa.Integer(),
            sa.ForeignKey("ideas.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            primary_key=True,
        ),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_idea_votes_idea_id", "idea_votes", ["idea_id"])


def downgrade() -> None:
    op.drop_index("ix_idea_votes_idea_id", table_name="idea_votes")
    op.drop_table("idea_votes")
    op.drop_column("ideas", "published_message_id")
    op.drop_column("ideas", "published_chat_id")
    op.drop_column("chats", "auto_publish")
