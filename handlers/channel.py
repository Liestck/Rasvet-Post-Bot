# channel | Модуль для работы с каналами | Rasvet Post Bot
import asyncio

from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.states import ChannelStates
from app.database.queries import Channels, Users
from app.keyboards import AuxiliaryKeyboards, ChannelKeyboards
from app.messages import BotMsg
from app.utils.logger import Logger

router = Router()

# Добавление канала
# =============================================
@router.callback_query(lambda c: c.data == "add_channel")
async def add_channel_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):

    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    except Exception:
        pass

    msg1 = await callback.message.answer(
        BotMsg.Channel.add_1,
        parse_mode="HTML",
        reply_markup=ChannelKeyboards.invite_bot()
    )

    msg2 = await callback.message.answer(
        BotMsg.Channel.add_2,
        parse_mode="HTML",
        reply_markup=AuxiliaryKeyboards.cancel()
    )

    await state.update_data(messages_to_delete=[msg1.message_id, msg2.message_id])
    await state.set_state(ChannelStates.waiting_for_username)
    await callback.answer()

@router.message(ChannelStates.waiting_for_username)
async def process_add_channel(message: Message, state: FSMContext, session, bot: Bot):

    username = message.text.strip()
    
    data = await state.get_data()
    msg_ids = data.get("messages_to_delete", [])

    # Очистка
    for msg_id in msg_ids:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass

    msg_ids = [message.message_id]

    channels = Channels(session)
    users = Users(session)
    user = await users.get_by_tg_id(message.from_user.id)

    # Проверка на отмену
    if username.lower() in ["отмена", "cancel", "✖️ отменить"]:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception:
            pass

        msgd = await message.answer(BotMsg.Channel.cancel_add, parse_mode="HTML")

        await asyncio.sleep(1.5)

        try:
            await bot.delete_message(chat_id=msgd.chat.id, message_id=msgd.message_id)
        except Exception:
            pass

        await state.clear()

        # Список каналов
        return await message.answer(
            BotMsg.Channel._list,
            parse_mode="HTML",
            reply_markup=ChannelKeyboards._list(
                await channels.get_user_channels(user.tg_id),
                await channels.can_add(user.tg_id, user.perm)
            )
        )

    # Проверка @username
    if not username.startswith("@"):
        msg = await message.answer(
            BotMsg.Channel.incorrect_channel_name,
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        return await state.update_data(messages_to_delete=msg_ids)
        

    # Получаем канал и права
    try:
        channel = await bot.get_chat(username)
        try:
            member = await bot.get_chat_member(channel.id, bot.id)
            can_post = member.can_post_messages if member else False
        except Exception:
            can_post = False

        if not can_post:
            msg = await message.answer(
                BotMsg.Channel.no_rights,
                parse_mode="HTML"
            )
            msg_ids.append(msg.message_id)
            return await state.update_data(messages_to_delete=msg_ids)

    except Exception:
        msg = await message.answer(
            BotMsg.Channel.not_found_channel_name,
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        return await state.update_data(messages_to_delete=msg_ids)
        

    # Проверка лимита
    can_add = await channels.can_add(user.tg_id, user.perm)
    if not can_add:
        await message.answer(BotMsg.Channel.limitation, parse_mode="HTML")
        return await state.clear()

    # Проверка на дубликат
    if any(c.channel_id == channel.id for c in await channels.get_user_channels(user.tg_id)):
        msg = await message.answer(
            BotMsg.channel.duplicate,
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        return await state.update_data(messages_to_delete=msg_ids)

    # Добавление канала
    await channels.add(
        channel.id,
        channel.title,
        user.tg_id,
        can_post,
        channel.username
    )

    # Очистка сообщений
    for msg_id in msg_ids:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass

    # Сообщение об успешном добавлении
    msg = await message.answer(
        BotMsg.Channel.successfully_add(channel),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    msg_ids.append(msg.message_id)

    # Обновление списка каналов
    msg_list = await message.answer(
        BotMsg.Channel._list,
        parse_mode="HTML",
        reply_markup=ChannelKeyboards._list(
            await channels.get_user_channels(user.tg_id),
            await channels.can_add(user.tg_id, user.perm)
        )
    )
    msg_ids.append(msg_list.message_id)

    await state.clear()

# Список каналов
# =============================================
@router.callback_query(lambda c: c.data.startswith("channels_main"))
async def channels_main(callback: CallbackQuery, session):

    channels = Channels(session)
    users = Users(session)
    user = await users.get_by_tg_id(callback.from_user.id)

    await callback.message.edit_text(
        BotMsg.Channel._list,
        parse_mode="HTML",
        reply_markup=ChannelKeyboards._list(
            await channels.get_user_channels(user.tg_id),
            await channels.can_add(user.tg_id, user.perm)
        )
    )

# Данные канала
# =============================================
@router.callback_query(lambda c: c.data.startswith("view_"))
async def view_channel_details(callback: CallbackQuery, session):

    channel_id = int(callback.data.split('_')[1])
    channel = await Channels(session).get_user_channel(callback.from_user.id, channel_id)

    if not channel:
        return await callback.answer(BotMsg.Channel.not_found, show_alert=True)

    await callback.message.edit_text(
        BotMsg.Channel.menu(channel),
        parse_mode="HTML",
        reply_markup=ChannelKeyboards.menu(channel.channel_id),
        disable_web_page_preview=True
    )

# Заменить канал
# =============================================
@router.callback_query(lambda c: c.data.startswith("edit_"))
async def replace_channel(callback: CallbackQuery, state: FSMContext, bot: Bot):

    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    except Exception:
        pass

    msg = await callback.message.answer(
        BotMsg.Channel.edit_new,
        parse_mode="HTML",
        reply_markup=AuxiliaryKeyboards.cancel()
    )
    
    await state.update_data(messages_to_delete=[msg.message_id])
    await state.set_state(ChannelStates.waiting_for_username_replace)
    await callback.answer()

@router.message(ChannelStates.waiting_for_username_replace)
async def process_replace_channel(message: Message, state: FSMContext, session, bot: Bot):
    username = message.text.strip()

    # Получаем предыдущие сообщения из FSM
    data = await state.get_data()
    msg_ids = data.get("messages_to_delete", [])

    # Удаляем все предыдущие сообщения
    for msg_id in msg_ids:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass

    # Добавляем текущее сообщение пользователя в список для удаления
    msg_ids = [message.message_id]

    channels = Channels(session)
    users = Users(session)
    user = await users.get_by_tg_id(message.from_user.id)

    # Если пользователь хочет отменить
    # =================================
    if username.lower() in ["отмена", "cancel", "✖️ отменить"]:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception:
            pass

        msgd = await message.answer(BotMsg.Channel.cancel_replace, parse_mode="HTML", reply_markup=None )
        await asyncio.sleep(1.5)
        try:
            await bot.delete_message(chat_id=msgd.chat.id, message_id=msgd.message_id)
        except Exception:
            pass

        await state.clear()

        await message.answer(
            BotMsg.Channel._list,
            parse_mode="HTML",
            reply_markup=ChannelKeyboards._list(
                await channels.get_user_channels(user.tg_id),
                await channels.can_add(user.tg_id, user.perm)
            )
        )
        return

    # Проверка @username
    if not username.startswith("@"):
        msg = await message.answer(
            "<b>⚠️ Ошибка!</b>\nВведите @username нового канала",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Получаем канал и права
    try:
        channel = await bot.get_chat(username)
        try:
            member = await bot.get_chat_member(channel.id, bot.id)
            can_post = member.can_post_messages if member else False
        except Exception:
            can_post = False
    except Exception:
        msg = await message.answer(
            "<b>⚠️ Такого канала не существует</b>\n\n<blockquote>Введите @username нового канала</blockquote>",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Получаем текущие активные каналы пользователя
    user_channels = await channels.get_user_channels(user.tg_id)
    if not user_channels:
        await state.clear()
        return

    current_channel = user_channels[0]  # первый активный канал

    # Проверка идентичного канала
    if current_channel.channel_id == channel.id:
        msg = await message.answer(
            "<b>⚠️ Вы не можете заменить канал на идентичный</b>\n<blockquote>Введите @username нового канала</blockquote>",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Проверка: канал уже есть в списке
    if any(c.channel_id == channel.id for c in user_channels):
        msg = await message.answer(
            "<b>⚠️ Этот канал уже подключён в вашем списке!</b>\n\n<blockquote>Введите @username нового канала</blockquote>",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Замена канала
    current_channel.channel_id = channel.id
    current_channel.title = channel.title
    current_channel.can_post = can_post
    current_channel.enabled = True
    await session.commit()

    # Очистка сообщений
    for msg_id in msg_ids:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass

    # Сообщение об успешной замене
    msg = await message.answer(
        f"<b>✅ Канал успешно добавлен!</b>\n\n<blockquote>{chat.title}</blockquote>",
        parse_mode="HTML",
        reply_markup=None 
    )
    msg_ids.append(msg.message_id)

    keyboard_msg = await message.answer(
        BotMsg.Channel._list,
        parse_mode="HTML",
        reply_markup=ChannelKeyboards._list(
            await channels.get_user_channels(user.tg_id),
            await channels.can_add(user.tg_id, user.perm)
        )
    )
    msg_ids.append(keyboard_msg.message_id)

    await state.clear()

# Удалить канал
# =============================================
@router.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_channel_callback(callback: CallbackQuery, session):

    try:
        channel_id = int(callback.data.split("_")[1])
    except ValueError:
        return await callback.answer(BotMsg.Channel.incorrect_data, show_alert=True)

    channel = await Channels(session).get_user_channel(callback.from_user.id, channel_id)

    if not channel:
        return await callback.answer(BotMsg.Channel.not_found, show_alert=True)

    # Клавиатура подтверждения
    await callback.message.edit_text(
        BotMsg.Channel.confirm_delete(channel),
        parse_mode="HTML",
        reply_markup=ChannelKeyboards.confirm_delete(channel),
        disable_web_page_preview=True
    )

    await callback.answer()

# Подтверждение
# =============================================
@router.callback_query(lambda c: c.data.startswith("delete-confirm_"))
async def delete_confirm_callback(callback: CallbackQuery, session):

    user_answer = bool(int(callback.data.split('_')[1][:1]))
    channel_id = int(callback.data.split('_')[1][1:])

    channels = Channels(session)
    users = Users(session)
    
    user = await users.get_by_tg_id(callback.from_user.id)
    channel = await Channels(session).get_user_channel(callback.from_user.id, channel_id)

    if not channel:
        return await callback.answer(BotMsg.Channel.not_found, show_alert=True)

    # Пользователь ПОДТВЕРДИЛ удаление
    if user_answer:
        channel.enabled = False
        await session.commit()

        Logger.Channel.delete(channel, callback)

        await callback.answer(BotMsg.Channel.delete)

        await callback.message.edit_text(
            BotMsg.Channel._list,
            parse_mode="HTML",
            reply_markup=ChannelKeyboards._list(
                await channels.get_user_channels(user.tg_id),
                await channels.can_add(user.tg_id, user.perm)
            ),
            disable_web_page_preview=True
        )

    # Пользователь ОТМЕНИЛ удаление
    else:
        await callback.message.edit_text(
            BotMsg.Channel.menu(channel),
            parse_mode="HTML",
            reply_markup=ChannelKeyboards.menu(channel.channel_id),
            disable_web_page_preview=True
        )