"""Voting on published ideas: publish to chat + accept up/down votes."""
import html
import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chat, Idea, IdeaVote
from app.services.ideas import TAGS_BY_KEY

log = logging.getLogger(__name__)


def vote_keyboard(idea_id: int, up: int, down: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"👍 {up}", callback_data=f"vote:up:{idea_id}"
                ),
                InlineKeyboardButton(
                    text=f"👎 {down}", callback_data=f"vote:down:{idea_id}"
                ),
            ]
        ]
    )


def published_text(idea: Idea) -> str:
    """Anonymized version posted to the source chat for voting."""
    tag = TAGS_BY_KEY.get(idea.tag) or TAGS_BY_KEY["other"]
    body = html.escape(idea.text or "")
    return (
        f"💡 <b>Идея на голосование</b>  ·  {tag.icon} {tag.label}\n"
        f"━━━━━━━━━━━━\n"
        f"{body}\n"
        f"━━━━━━━━━━━━\n"
        f"<i>Поддержи или возрази 👇</i>"
    )


async def get_vote_totals(
    session: AsyncSession, idea_id: int
) -> tuple[int, int]:
    result = await session.execute(
        select(
            func.coalesce(
                func.sum(case((IdeaVote.value > 0, 1), else_=0)), 0
            ),
            func.coalesce(
                func.sum(case((IdeaVote.value < 0, 1), else_=0)), 0
            ),
        ).where(IdeaVote.idea_id == idea_id)
    )
    row = result.one()
    return int(row[0] or 0), int(row[1] or 0)


async def record_vote(
    session: AsyncSession, idea_id: int, user_id: int, value: int
) -> tuple[int, int, str]:
    """Toggle/switch a user's vote on an idea.

    Returns (up, down, action) where action is one of
    'added' | 'removed' | 'switched'.
    """
    if value not in (1, -1):
        raise ValueError("value must be +1 or -1")

    result = await session.execute(
        select(IdeaVote).where(
            IdeaVote.idea_id == idea_id,
            IdeaVote.user_id == user_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing is None:
        session.add(IdeaVote(idea_id=idea_id, user_id=user_id, value=value))
        action = "added"
    elif existing.value == value:
        await session.delete(existing)
        action = "removed"
    else:
        existing.value = value
        action = "switched"

    await session.commit()
    up, down = await get_vote_totals(session, idea_id)
    return up, down, action


async def publish_idea_to_chat(
    bot: Bot, session: AsyncSession, idea: Idea, chat: Chat
) -> Message | None:
    """Post an anonymized voting card into the source chat."""
    if idea.published_message_id is not None:
        return None  # already published

    text = published_text(idea)
    keyboard = vote_keyboard(idea.id, 0, 0)

    try:
        sent = await bot.send_message(chat.chat_id, text, reply_markup=keyboard)
    except Exception as exc:  # noqa: BLE001
        log.warning("publish idea %s to chat %s failed: %s", idea.id, chat.chat_id, exc)
        return None

    idea.published_chat_id = chat.chat_id
    idea.published_message_id = sent.message_id
    await session.commit()
    return sent
