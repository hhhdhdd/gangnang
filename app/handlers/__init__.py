from aiogram import Dispatcher

from app.handlers import common


def register_handlers(dp: Dispatcher) -> None:
    dp.include_router(common.router)
