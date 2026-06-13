"""chats.song_enabled, song_cron, last_song_sent_at

Revision ID: 0008_chats_song_schedule
Revises: 0007_chat_messages_and_songs
Create Date: 2026-06-13

Adds per-chat daily-song scheduling to the ``chats`` table:

- ``song_enabled``     — opt-in toggle for the automatic song-of-the-day.
- ``song_cron``        — crontab expression (TZ = global settings.tz)
                         that fires ``run_scheduled_song_for_chat``.
- ``last_song_sent_at``— bookkeeping timestamp of the last successful
                         scheduled post (for UI / debugging).

A chat is scheduled by ``IdeaScheduler`` only when
``is_active AND song_enabled AND song_cron`` are all set. The manual
``/song_now`` and ``/musicmenu`` triggers ignore these columns.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_chats_song_schedule"
down_revision: Union[str, None] = "0007_chat_messages_and_songs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column(
            "song_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "chats",
        sa.Column("song_cron", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "chats",
        sa.Column(
            "last_song_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("chats", "last_song_sent_at")
    op.drop_column("chats", "song_cron")
    op.drop_column("chats", "song_enabled")
