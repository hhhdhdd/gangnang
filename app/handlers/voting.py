"""Vote up/down on published ideas (callback handler)."""
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.voting import record_vote, vote_keyboard

log = logging.getLogger(__name__)

router = Router(name="voting")


@router.callback_query(F.data.startswith("vote:"))
async def cb_vote(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return

    direction = parts[1]
    if direction not in ("up", "down"):
        await callback.answer()
        return

    try:
        idea_id = int(parts[2])
    except ValueError:
        await callback.answer()
        return

    value = 1 if direction == "up" else -1
    up, down, action = await record_vote(
        session, idea_id, callback.from_user.id, value
    )

    icon = "👍" if direction == "up" else "👎"
    msg = {
        "added": f"{icon} Учтено",
        "switched": f"{icon} Учтено (переголосовал)",
        "removed": f"{icon} Снято",
    }.get(action, "✅")
    await callback.answer(msg)

    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_reply_markup(
                reply_markup=vote_keyboard(idea_id, up, down)
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("edit vote keyboard failed: %s", exc)
