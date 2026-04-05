# main | Rasvet Post Bot
import asyncio
from aiogram import Bot, Dispatcher

from app.config import Config

from app.database.models import Base
from app.database.db import engine
from app.database.middleware import DbSessionMiddleware
from app.utils.logger import Logger
from app.handlers.channel import router as channel_router
from app.handlers.post import router as post_router
from app.handlers.format import router as format_router
from app.handlers.start import router as start_router
from app.utils.ping import router as ping_router


async def main():
    
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_routers(
        channel_router,
        post_router,
        format_router,
        start_router,
        ping_router,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Logger.Bot.bot_start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()
        Logger.Bot.bot_stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
