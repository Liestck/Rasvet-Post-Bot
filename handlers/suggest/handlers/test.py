# app.handlers.suggest.handlers.test | Тестовый хендлер предложки | Rasvet Post Bot
from aiogram import Router, F
from aiogram.types import Message


router = Router()


# Проверка состояния бота
# =============================================
@router.message(F.text == "ping")
async def ping(message: Message):
    await message.answer("🏓 Pong...\n\n<blockquote>Бот предложки в рабочем состоянии!</blockquote>", parse_mode="HTML")


# test echo
# =============================================
@router.message()
async def echo(message: Message):
    await message.answer(f"📩: {message.text}")