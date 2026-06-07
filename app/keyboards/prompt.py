from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def prompt_keyboard(bot_username: str, chat_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard attached to the periodic 'share an idea' prompt."""
    deep_link = f"https://t.me/{bot_username}?start=idea_{chat_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ В личку", url=deep_link),
                InlineKeyboardButton(
                    text="💬 Ответить здесь", callback_data="idea:hint"
                ),
            ],
        ]
    )


def anonymity_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🙈 Анонимно", callback_data="anon:1"),
                InlineKeyboardButton(text="✍️ С именем", callback_data="anon:0"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="anon:cancel")],
        ]
    )


def owner_card_keyboard(
    idea_id: int,
    *,
    can_publish: bool = False,
    is_published: bool = False,
    vote_up: int = 0,
    vote_down: int = 0,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="⭐", callback_data=f"card:star:{idea_id}"),
            InlineKeyboardButton(text="✅", callback_data=f"card:read:{idea_id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"card:archive:{idea_id}"),
        ],
        [
            InlineKeyboardButton(
                text="✉️ Ответить автору",
                callback_data=f"card:reply:{idea_id}",
            )
        ],
    ]

    if is_published:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📢 Опубликовано · 👍 {vote_up}  👎 {vote_down}",
                    callback_data=f"card:refresh:{idea_id}",
                )
            ]
        )
    elif can_publish:
        rows.append(
            [
                InlineKeyboardButton(
                    text="📢 Опубликовать в чат",
                    callback_data=f"card:publish:{idea_id}",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)
