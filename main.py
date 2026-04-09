# main | Rasvet Post Bot
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from sqlalchemy import select

from app.config import Config
from app.database.models import Base, Channel
from app.database.db import engine, SessionFactory
from app.database.middleware import DbSessionMiddleware

from app.utils.logger import Logger
from app.utils.crypto import crypto

from app.handlers.channel import router as channel_router
from app.handlers.post import router as post_router
from app.handlers.format import router as format_router
from app.handlers.suggest.main import router as suggest_router
from app.handlers.start import router as start_router
from app.utils.ping import router as ping_router

from app.handlers.suggest.manager import suggest_runner


async def main():

    bot = Bot(token=Config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_routers(
        channel_router,
        post_router,
        format_router,
        start_router,
        ping_router,
        suggest_router
    )

    # Загрузка БД
    # =============================================
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Запуск всех предложек
    # =============================================
    async with SessionFactory() as session:

        result = await session.execute(
            select(Channel).where(Channel.suggest_token.isnot(None))
        )

        channels = result.scalars().all()

        for ch in channels:

            try:
                token = crypto.decrypt(ch.suggest_token)

                await suggest_runner.start_bot(
                    channel_id=ch.channel_id,
                    token=token
                )

                Logger.Suggest.bot_start(ch.channel_id)

            except Exception as e:
                Logger.Suggest.bot_error(ch.channel_id, e)


    Logger.Bot.bot_start()

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    finally:
        # Остановка всех предложек
        await suggest_runner.stop_all()

        await bot.session.close()
        await engine.dispose()

        Logger.Bot.bot_stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass