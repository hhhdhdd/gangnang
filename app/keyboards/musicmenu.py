"""Inline keyboards + text rendering for the unified ``/musicmenu`` admin home.

When an admin runs ``/musicmenu`` in DM (or any callback returns
``home``/``mm:home``), this is the screen they land on — one place for
every admin-facing setting, grouped into sections:

  🎵 Генерация — Suno · OpenRouter · длительность · стили · «сейчас»
  🗂 Песни     — архив всех песен · статистика генераций
  ⚙️ Управление — чаты · идеи · админы · тишина · логи

Callback-data namespace
-----------------------

``mm:*`` for entries owned by this screen (``mm:home``, ``mm:styles``,
``mm:gen_pick``, ``mm:archive``, ``mm:stats``). Buttons that open
existing sections re-use those sections' own namespaces
(``suno:home``, ``llm:home``, ``logs:home``, ``qh:open``,
``ideas:filter:new``, ``admin:list``, ``chat:list:0``,
``suno:duration_open``) so a tap goes straight into the existing
handler with no extra plumbing.
"""
from __future__ import annotations

import html
from typing import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def musicmenu_home_keyboard(
    *,
    chat_count: int,
    admin_count: int,
    suno_ok: bool,
    llm_ok: bool,
    suno_model: str,
    llm_model_label: str,
    target_duration_label: str,
) -> InlineKeyboardMarkup:
    """Unified admin home keyboard, grouped into the three sections
    mirrored by :func:`render_musicmenu_home_text`.

    The 🟢/🔴 indicators on Suno / OpenRouter reflect whether each
    provider's API key is set — the one bit of state that silently
    breaks generation, so it's surfaced on the entry screen.
    """
    suno_label = (
        f"🎚 Suno · {'🟢' if suno_ok else '🔴'} · {suno_model}"
    )[:64]
    llm_label = (
        f"🤖 OpenRouter · {'🟢' if llm_ok else '🔴'} · {llm_model_label}"
    )[:64]

    rows: list[list[InlineKeyboardButton]] = [
        # ── 🎵 Генерация песен ──
        [InlineKeyboardButton(text=suno_label, callback_data="suno:home")],
        [InlineKeyboardButton(text=llm_label, callback_data="llm:home")],
        [
            InlineKeyboardButton(
                text=f"🎯 Длительность · {target_duration_label}",
                callback_data="suno:duration_open",
            ),
            InlineKeyboardButton(
                text="🎼 Стили чатов",
                callback_data="mm:styles",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎵 Сгенерировать песню дня",
                callback_data="mm:gen_pick",
            ),
        ],
        # ── 🗂 Песни ──
        [
            InlineKeyboardButton(
                text="🎼 Архив песен",
                callback_data="mm:archive",
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="mm:stats",
            ),
        ],
        # ── ⚙️ Управление ботом ──
        [
            InlineKeyboardButton(
                text=f"📋 Чаты ({chat_count})",
                callback_data="chat:list:0",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💡 Идеи",
                callback_data="ideas:filter:new",
            ),
            InlineKeyboardButton(
                text=f"👥 Админы ({admin_count})",
                callback_data="admin:list",
            ),
        ],
        [
            InlineKeyboardButton(text="🌙 Тишина", callback_data="qh:open"),
            InlineKeyboardButton(text="📜 Логи", callback_data="logs:home"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_musicmenu_home_text(
    *,
    chat_count: int,
    admin_count: int,
    suno_ok: bool,
    llm_ok: bool,
    suno_model: str,
    llm_model_label: str,
    target_duration_label: str,
) -> str:
    """Body text above the keyboard, grouped into the same sections as
    the buttons so the screen reads top-to-bottom."""
    suno_status = "🟢 ключ задан" if suno_ok else "🔴 нет ключа"
    llm_status = "🟢 ключ задан" if llm_ok else "🔴 нет ключа"
    ready_line = (
        "✅ Всё готово к генерации."
        if (suno_ok and llm_ok)
        else "⚠️ Для генерации нужны оба ключа (Suno + OpenRouter)."
    )
    return (
        "🎵 <b>Музыкальное меню — управление ботом</b>\n"
        f"{ready_line}\n\n"
        "━━━━━━  🎵 Генерация  ━━━━━━\n"
        f"🎚 <b>Suno</b> · {suno_status} · "
        f"<code>{html.escape(suno_model)}</code>\n"
        f"🤖 <b>OpenRouter</b> · {llm_status} · "
        f"<code>{html.escape(llm_model_label)}</code>\n"
        f"🎯 <b>Длительность</b> · "
        f"<code>{html.escape(target_duration_label)}</code>\n"
        "🎼 Стиль — отдельно для каждого чата\n\n"
        "━━━━━━  🗂 Песни  ━━━━━━\n"
        "Архив всех песен · статистика генераций\n\n"
        "━━━━━━  ⚙️ Управление  ━━━━━━\n"
        f"📋 Чатов: <b>{chat_count}</b>  ·  👥 Админов: <b>{admin_count}</b>\n"
        "Идеи · тишина · логи\n\n"
        "Тапни раздел ниже 👇"
    )


def musicmenu_styles_keyboard(
    chats: Iterable,
) -> InlineKeyboardMarkup:
    """Chat picker for "🎼 Стили чатов" — opens
    :func:`app.keyboards.music.music_menu_keyboard` for the chosen chat
    via the existing ``music:menu_open:<chat_id>`` callback.
    """
    rows: list[list[InlineKeyboardButton]] = []
    for chat in chats:
        title = (chat.title or str(chat.chat_id))[:50]
        emoji = "🟢" if chat.is_active else "🟡"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{emoji} {title}"[:64],
                    callback_data=f"music:menu_open:{chat.chat_id}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="mm:home")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def musicmenu_back_keyboard() -> InlineKeyboardMarkup:
    """Single ⬅️ back-to-home button (used by inline sub-views like stats)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="mm:home")]
        ]
    )
