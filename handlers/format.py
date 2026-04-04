# handlers.format | Настройка формата постов | Rasvet Post Bot
import asyncio

from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.database.queries import Channels, Format
from app.states.format import FormatStates
from app.messages import BotMsg
from app.keyboards import FormatKeyboards, ChannelKeyboards
from app.utils.functions import Converting


router = Router()


# Сборщик preview текста
# =============================================
def build_preview_text(channel, mode: str = "full"):

    up_text = channel.up_text
    down_text = channel.down_text

    up_block = (
        f"1️⃣ {up_text}\n"
        if up_text
        else '<a href="t.me/RasvetPost_bot">1️⃣ Верхний текст <b>пуст</b></a>\n'
    )

    down_block = (
        f"2️⃣ {down_text}"
        if down_text
        else '<a href="t.me/RasvetPost_bot">2️⃣ Нижний текст <b>пуст</b></a>'
    )

    if mode == "up":
        return up_block

    if mode == "down":
        return down_block

    if mode == "full":
        return (
            up_block +
            f"Это пост в канале <b>{channel.title}!</b> 😀\n" +
            down_block
        )

    raise ValueError(f"Unknown mode: {mode}")


# Меню форматирования постов
# =============================================
@router.callback_query(lambda c: c.data.startswith("post_format_main_"))
async def format_menu_handler(callback: CallbackQuery, state: FSMContext, session):

    channel_id = int(callback.data.split("_")[-1])
    channel = await Channels(session).get_user_channel(callback.from_user.id, channel_id)

    await callback.answer()

    manual_msg = await callback.message.edit_text(
        BotMsg.Format.manual_full,
        parse_mode="HTML",
    )

    preview_msg = await callback.message.answer(
        build_preview_text(channel),
        parse_mode="HTML",
        reply_markup=FormatKeyboards.menu(channel_id),
        disable_web_page_preview=True
    )

    await state.set_state(FormatStates.menu)

    await state.update_data(
        channel_id=channel_id,
        main_menu_msg_id=callback.message.message_id,
        preview_msg_id=preview_msg.message_id,
        manual_msg_id=manual_msg.message_id
    )


# Выход в меню канала
# =============================================
@router.callback_query(lambda c: c.data.startswith("return_"))
async def return_handler(callback: CallbackQuery, state: FSMContext, bot: Bot, session):

    channel_id = int(callback.data.split("_")[-1])
    channel = await Channels(session).get_user_channel(callback.from_user.id, channel_id)

    data = await state.get_data()

    await callback.answer()

    main_msg_id = data.get("main_menu_msg_id")
    preview_msg_id = data.get("preview_msg_id")

    if preview_msg_id:
        try:
            await bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=preview_msg_id
            )
        except:
            pass

    if main_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=main_msg_id,
                text=BotMsg.Channel.menu(channel),
                parse_mode="HTML",
                reply_markup=ChannelKeyboards.menu(channel.channel_id)
            )
        except:
            pass

    await state.clear()


# Меню блока
# =============================================
@router.callback_query(lambda c: c.data.startswith('post_format_text_'))
async def format_text_handler(callback: CallbackQuery, state: FSMContext, bot: Bot, session):

    channel_id = int(callback.data.split("_")[-1])
    channel = await Channels(session).get_user_channel(callback.from_user.id, channel_id)
    
    text_pos = str(callback.data.split("_")[-2])
    data = await state.get_data()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=data.get('manual_msg_id'),
        text=BotMsg.Format.manual_short,
        parse_mode="HTML"
    )

    await callback.message.edit_text(
        text=build_preview_text(channel, mode=text_pos),
        parse_mode="HTML",
        reply_markup=FormatKeyboards.format_text(channel_id, text_pos),
        disable_web_page_preview=True
    )


# Выход в меню форматирования
# =============================================
@router.callback_query(lambda c: c.data.startswith('post_format_return_'))
async def format_text_handler(callback: CallbackQuery, state: FSMContext, bot: Bot, session):

    channel_id = int(callback.data.split("_")[-1])
    channel = await Channels(session).get_user_channel(callback.from_user.id, channel_id)
    
    data = await state.get_data()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=data.get('manual_msg_id'),
        text=BotMsg.Format.manual_full,
        parse_mode="HTML"
    )

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=data.get('preview_msg_id'),
        text=build_preview_text(channel),
        parse_mode="HTML",
        reply_markup=FormatKeyboards.menu(channel_id),
        disable_web_page_preview=True
    )

    await state.set_state(FormatStates.menu)


# Редактирование блока
# =============================================
@router.callback_query(lambda c: c.data.startswith('post_format_edit_'))
async def edit_text_start(callback: CallbackQuery, state: FSMContext):

    _, _, _, channel_id, text_pos = callback.data.split("_")
    channel_id = int(channel_id)

    await state.set_state(FormatStates.editing)

    prompt_msg = await callback.message.answer(
        f"Введите текст {'верхнего' if text_pos == 'up' else 'нижнего'} блока 👇"
    )

    await state.update_data(
        channel_id=channel_id,
        text_pos=text_pos,
        prompt_msg_id=prompt_msg.message_id
    )

    await callback.answer()


@router.message(FormatStates.editing)
async def process_text(message: Message, state: FSMContext, session, bot: Bot):

    data = await state.get_data()

    channel_id = data.get("channel_id")
    text_pos = data.get("text_pos")
    prompt_msg_id = data.get("prompt_msg_id")

    format_q = Format(session)
    channels_q = Channels(session)

    await format_q.update_text(
        owner_tg_id=message.from_user.id,
        channel_id=channel_id,
        text_pos=text_pos,
        text=message.html_text
    )

    channel = await channels_q.get_user_channel(message.from_user.id, channel_id)

    try:
        await message.delete()

        if prompt_msg_id:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=prompt_msg_id
            )
    except:
        pass

    success_msg = await message.answer(BotMsg.Format.successfully_edit, parse_mode="HTML")

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=data.get("preview_msg_id"),
        text=build_preview_text(channel, mode=text_pos),
        parse_mode="HTML",
        reply_markup=FormatKeyboards.format_text(channel_id, text_pos),
        disable_web_page_preview=True
    )

    await asyncio.sleep(3)

    try:
        await success_msg.delete()
    except:
        pass

    await state.set_state(FormatStates.menu)


# Очистка блока
# =============================================
@router.callback_query(lambda c: c.data.startswith('post_format_delete_'))
async def delete_text_handler(callback: CallbackQuery, state: FSMContext, session, bot: Bot):

    _, _, _, channel_id, text_pos = callback.data.split("_")
    channel_id = int(channel_id)

    format_q = Format(session)
    channels_q = Channels(session)

    await format_q.update_text(
        owner_tg_id=callback.from_user.id,
        channel_id=channel_id,
        text_pos=text_pos,
        text=None
    )

    channel = await channels_q.get_user_channel(callback.from_user.id, channel_id)

    data = await state.get_data()

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=data.get("preview_msg_id"),
        text=build_preview_text(channel, mode=text_pos),
        parse_mode="HTML",
        reply_markup=FormatKeyboards.format_text(channel_id, text_pos),
        disable_web_page_preview=True
    )

    await callback.answer("Очищено ✅")