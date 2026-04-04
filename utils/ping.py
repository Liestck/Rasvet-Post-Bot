
# utils.ping | Проверка работоспособности бота | Rasvet Post Bot
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


router = Router()


@router.message(Command(commands=["ping", "пинг"]))
async def ping_handler(message: Message):
    await message.answer("🏓 Pong...\n\n<blockquote>Бот в рабочем состоянии!</blockquote>", parse_mode="HTML")