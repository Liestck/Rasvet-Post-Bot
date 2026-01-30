import asyncio
from aiogram import Bot, Dispatcher

from app.config import Config
from app.handlers.start import router as start_router
from app.database.models import Base
from app.database.db import engine
from app.database.middleware import DbSessionMiddleware
from app.utils.logger import bot_start, bot_stop
from app.handlers.channel import router as channel_router


async def main():
    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_router(start_router)
    dp.include_router(channel_router)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot_start()  # 🚀 старт

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        bot_stop()  # 🛑 остановка


if __name__ == "__main__":
    asyncio.run(main())
