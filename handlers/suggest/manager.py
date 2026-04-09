# app.handlers.suggest.manager | Менеджер ботов предложки | Rasvet Post Bot
import asyncio
from aiogram import Bot, Dispatcher

from app.handlers.suggest.handlers.test import router as suggest_test_router


class SuggestBotRunner:

    def __init__(self):
        self.tasks: dict[int, asyncio.Task] = {}
        self.bots: dict[int, Bot] = {}

    # Запуск предложки
    # =============================================
    async def start_bot(self, channel_id: int, token: str):
        if channel_id in self.tasks:
            return

        bot = Bot(token=token)
        dp = Dispatcher()

        # Handlers предложки
        # =============================================
        dp.include_router(suggest_test_router)

        async def runner():
            try:
                await dp.start_polling(bot)
            finally:
                await bot.session.close()

        task = asyncio.create_task(runner())

        self.tasks[channel_id] = task
        self.bots[channel_id] = bot

    # Остановка предложки
    # =============================================
    async def stop_bot(self, channel_id: int):
        task = self.tasks.pop(channel_id, None)
        bot = self.bots.pop(channel_id, None)

        if task:
            task.cancel()

        if bot:
            await bot.session.close()

    # Отсановка всех предложек
    # =============================================
    async def stop_all(self):
        for channel_id in list(self.tasks.keys()):
            await self.stop_bot(channel_id)

suggest_runner = SuggestBotRunner()