from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.database.queries import Users, Channels
from app.keyboards import StartKeyboard

router = Router()


@router.message(Command(commands=["start", "channels"]))
async def start_handler(message: Message, state: FSMContext, session):
    """Обработка команды /start"""
    users = Users(session)
    channels = Channels(session)

    # Получаем или создаем пользователя
    user = await users.get_or_create(message.from_user)

    # Список каналов пользователя
    user_channels = await channels.get_user_channels(user.tg_id)

    # Проверяем, можно ли добавить новый канал
    can_add_channel = await channels.can_add(user.tg_id, user.perm)

    # Формируем текст
    if not user_channels:
        text = (
            '<b><a href="t.me/RasvetPost_bot">👋 Привет!</a></b>\n\n'
            "<b>Я помогу тебе вести Telegram-канал:</b>\n"
            "<blockquote>• принимать предложку\n"
            "• публиковать посты</blockquote>\n\n"
            "Начнём с подключения канала 👇"
        )
    else:
        text = "<b>Ваши каналы 👇</b>"

    # Генерируем клавиатуру
    keyboard = StartKeyboard.get_channels_keyboard(user_channels, can_add_channel)

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )