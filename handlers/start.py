# handlers.start | Хендлер стартовой команды
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.database.queries import Users, Channels
from app.keyboards import ChannelKeyboards
from app.messages import BotMsg


router = Router()


@router.message(Command(commands=["start", "channels", "каналы"]))
async def start_handler(message: Message, session):
    """ Вызываем стартовое сообщение / Список каналов """

    users = Users(session)
    channels = Channels(session)

    user = await users.get_or_create(message.from_user)
    user_channels = await channels.get_user_channels(user.tg_id)
    can_add_channel = await channels.can_add(user.tg_id, user.perm)

    # Выборка текста ( Приветствие / Список каналов )
    if not user_channels:
        msg = BotMsg.Bot.welcome
    else:
        msg = BotMsg.Channel._list

    # Список каналов
    await message.answer(
        text=msg,
        parse_mode="HTML",
        reply_markup=ChannelKeyboards._list(user_channels, can_add_channel),
        disable_web_page_preview=True
    )