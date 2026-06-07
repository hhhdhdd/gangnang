import asyncio
import logging

from app.bot import build_bot, build_dispatcher
from app.config import settings
from app.handlers import register_handlers


async def main() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    log = logging.getLogger("ideabottg")

    bot = build_bot()
    dp = build_dispatcher()
    register_handlers(dp)

    me = await bot.get_me()
    log.info("Starting bot @%s (id=%s)", me.username, me.id)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
