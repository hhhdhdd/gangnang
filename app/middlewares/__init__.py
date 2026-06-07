from aiogram import Dispatcher

from app.middlewares.db import DbSessionMiddleware


def register_middlewares(dp: Dispatcher) -> None:
    middleware = DbSessionMiddleware()
    dp.message.middleware(middleware)
    dp.callback_query.middleware(middleware)
    dp.my_chat_member.middleware(middleware)
    dp.chat_member.middleware(middleware)
