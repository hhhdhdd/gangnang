"""DB-backed tests for the new song service helpers.

Covers ``has_song_on_date`` (scheduled-song dedup), ``song_stats``
(/song_stats), and ``purge_chat_history`` (/song_purge). Uses naive
UTC datetimes for determinism — SQLite stores DateTime tz-naive, and
the production tz-aware/UTC conversion lives in the caller
(``run_scheduled_song_for_chat``), not in these queries.
"""
from datetime import datetime, timedelta

import pytest

from app.models import Chat, ChatMessage, Song
from app.services.chat_messages import purge_chat_history
from app.services.songs import has_song_on_date, song_stats


async def _add_chat(session, chat_id: int) -> None:
    session.add(Chat(chat_id=chat_id, title=f"chat{chat_id}", is_active=True))
    await session.commit()


def _song(chat_id, task_id, when, status="success"):
    return Song(
        suno_task_id=task_id,
        model="V4_5",
        chat_id=chat_id,
        status=status,
        created_at=when,
    )


@pytest.mark.asyncio
async def test_has_song_on_date_true_within_window(session):
    await _add_chat(session, 100)
    now = datetime(2026, 6, 13, 12, 0, 0)
    session.add(_song(100, "t1", now))
    await session.commit()

    assert await has_song_on_date(
        session,
        chat_id=100,
        day_start_utc=now - timedelta(hours=12),
        day_end_utc=now + timedelta(hours=12),
    ) is True


@pytest.mark.asyncio
async def test_has_song_on_date_false_outside_window(session):
    await _add_chat(session, 101)
    now = datetime(2026, 6, 13, 12, 0, 0)
    session.add(_song(101, "t2", now))
    await session.commit()

    # window 10 days in the past -> no song there
    assert await has_song_on_date(
        session,
        chat_id=101,
        day_start_utc=now - timedelta(days=10),
        day_end_utc=now - timedelta(days=9),
    ) is False


@pytest.mark.asyncio
async def test_has_song_on_date_ignores_other_chats_and_failures(session):
    await _add_chat(session, 102)
    await _add_chat(session, 103)
    now = datetime(2026, 6, 13, 12, 0, 0)
    session.add(_song(103, "t3", now))                 # different chat
    session.add(_song(102, "t4", now, status="failed"))  # not success
    await session.commit()

    assert await has_song_on_date(
        session,
        chat_id=102,
        day_start_utc=now - timedelta(hours=12),
        day_end_utc=now + timedelta(hours=12),
    ) is False


@pytest.mark.asyncio
async def test_song_stats_counts(session):
    await _add_chat(session, 200)
    await _add_chat(session, 201)
    now = datetime.utcnow()
    session.add(_song(200, "s1", now))
    session.add(_song(200, "s2", now))
    session.add(_song(201, "s3", now))
    session.add(_song(200, "s4", now, status="failed"))  # excluded from total
    await session.commit()

    stats = await song_stats(session, days=30)
    assert stats["total"] == 3          # success only
    assert stats["recent"] == 3
    by_chat = dict(stats["by_chat"])
    assert by_chat[200] == 2
    assert by_chat[201] == 1
    by_status = dict(stats["by_status"])
    assert by_status.get("failed") == 1


@pytest.mark.asyncio
async def test_count_songs_for_chat_since(session):
    from datetime import datetime, timedelta

    from app.services.songs import count_songs_for_chat_since

    await _add_chat(session, 400)
    now = datetime.utcnow()
    session.add(_song(400, "c1", now))
    session.add(_song(400, "c2", now))
    session.add(_song(400, "c3", now - timedelta(days=2)))  # old
    session.add(_song(400, "c4", now, status="failed"))     # not success
    await session.commit()

    since = now - timedelta(hours=24)
    assert await count_songs_for_chat_since(session, 400, since) == 2
    await _add_chat(session, 300)
    for i in range(3):
        session.add(
            ChatMessage(
                chat_id=300,
                tg_message_id=i,
                user_id=1,
                username="u",
                full_name="U",
                text=f"msg {i}",
            )
        )
    await session.commit()

    deleted = await purge_chat_history(session, 300)
    assert deleted == 3
    # second purge is a no-op
    assert await purge_chat_history(session, 300) == 0
