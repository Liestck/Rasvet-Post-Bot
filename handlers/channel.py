from colorama import Fore, Style
import asyncio

from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.states.channel import ChannelStates
from app.database.queries import Channels, Users
from app.keyboards import StartKeyboard, AuxiliaryKeyboards


router = Router()

# Добавление канала
# =============================================
@router.callback_query(lambda c: c.data == "add_channel")
async def add_channel_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Начало добавления нового канала"""
    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    except Exception:
        pass

    msg = await callback.message.answer(
        "<b>Введите @username канала:</b>\n\n<blockquote>Например @mychannel</blockquote>",
        parse_mode="HTML",
        reply_markup=AuxiliaryKeyboards.cancel_keyboard()
    )
    await state.update_data(messages_to_delete=[msg.message_id])
    await state.set_state(ChannelStates.waiting_for_username)
    await callback.answer()

@router.message(ChannelStates.waiting_for_username)
async def process_add_channel(message: Message, state: FSMContext, session, bot: Bot):
    username = message.text.strip()
    
    data = await state.get_data()
    msg_ids = data.get("messages_to_delete", [])

    # Удаляем предыдущие сообщения
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

        msgd = await message.answer("<b>❌ Отмена добавления канала</b>", parse_mode="HTML")
        await asyncio.sleep(1.5)
        try:
            await bot.delete_message(chat_id=msgd.chat.id, message_id=msgd.message_id)
        except Exception:
            pass

        await state.clear()

        # Показать список каналов
        user_channels = await channels.get_user_channels(user.tg_id)
        can_add_channel = await channels.can_add(user.tg_id, user.perm)
        await message.answer(
            "<b>Ваши каналы 👇</b>",
            parse_mode="HTML",
            reply_markup=StartKeyboard.get_channels_keyboard(user_channels, can_add_channel)
        )
        return

    # Проверка @username
    if not username.startswith("@"):
        msg = await message.answer(
            "<b>⚠️ Ошибка!</b>\nВведите @username канала",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Получаем чат и права
    try:
        chat = await bot.get_chat(username)
        try:
            member = await bot.get_chat_member(chat.id, bot.id)
            can_post = member.can_post_messages if member else False
        except Exception:
            can_post = False
    except Exception:
        msg = await message.answer(
            "<b>⚠️ Такого канала не существует</b>\n\n<blockquote>Введите @username канала</blockquote>",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Проверка лимита
    can_add = await channels.can_add(user.tg_id, user.perm)
    if not can_add:
        await message.answer('<b>🚫 Вы достигли лимита каналов</b>', parse_mode="HTML")
        await state.clear()
        return

    # Проверка на дубликат
    user_channels = await channels.get_user_channels(user.tg_id)
    if any(c.channel_id == chat.id for c in user_channels):
        msg = await message.answer(
            "<b>⚠️ Этот канал уже подключён в вашем списке!</b>\n\n<blockquote>Введите @username канала</blockquote>",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Добавление канала
    await channels.add(chat.id, chat.title, user.tg_id, can_post)

    # Очистка сообщений
    for msg_id in msg_ids:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception:
            pass

    # Сообщение об успешном добавлении
    msg = await message.answer(
        f"<b>✅ Канал успешно добавлен!</b>\n\n<blockquote>{chat.title}</blockquote>",
        parse_mode="HTML"
    )
    msg_ids.append(msg.message_id)

    # Обновление списка каналов
    user_channels = await channels.get_user_channels(user.tg_id)
    can_add_channel = await channels.can_add(user.tg_id, user.perm)
    keyboard_msg = await message.answer(
        "<b>Ваши каналы 👇</b>",
        parse_mode="HTML",
        reply_markup=StartKeyboard.get_channels_keyboard(user_channels, can_add_channel)
    )
    msg_ids.append(keyboard_msg.message_id)

    await state.clear()

# Список каналов
# =============================================
@router.callback_query(lambda c: c.data.startswith("channels_main"))
async def channels_main(callback: CallbackQuery, session, bot: Bot):

    # Получение списка каналов пользователя
    channels = Channels(session)
    user_channels = await channels.get_user_channels(callback.from_user.id)

    # Обновляем список каналов
    users = Users(session)
    user = await users.get_by_tg_id(callback.from_user.id)
    user_channels = await channels.get_user_channels(user.tg_id)
    can_add_channel = await channels.can_add(user.tg_id, user.perm)
    keyboard = StartKeyboard.get_channels_keyboard(user_channels, can_add_channel)
    await callback.message.edit_text("<b>Ваши каналы 👇</b>", parse_mode="HTML", reply_markup=keyboard)

# Данные канала
# =============================================
@router.callback_query(lambda c: c.data.startswith("view_"))
async def view_channel_details(callback: CallbackQuery, session, bot: Bot):
    channel_id = int(callback.data.split('_')[1])

    users = Users(session)
    channels = Channels(session)

    # Получаем пользователя
    user = await users.get_by_tg_id(callback.from_user.id)
    if not user:
        return await callback.answer("❌ Пользователь не найден", show_alert=True)

    # Получаем каналы пользователя
    user_channels = await channels.get_user_channels(user.tg_id)

    # Ищем нужный канал
    channel = next(
        (c for c in user_channels if int(c.channel_id) == channel_id),
        None
    )

    if not channel:
        return await callback.answer('⚠️ Ошибка: Канал не найден', show_alert=True)

    # Формируем текст
    text = (
        f"<b><blockquote>{channel.title}</blockquote></b>\n\n"
        f"<b>ID канала: </b><code>{channel.channel_id}</code>\n"
        f"<b>Права на публикацию: </b>"
        f"{'✅' if channel.can_post else '❌'}\n"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=StartKeyboard.channel_actions(channel.channel_id)
    )

# Заменить канал
# =============================================
@router.callback_query(lambda c: c.data.startswith("edit_"))
async def replace_channel(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Начало редактирования канала"""
    try:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    except Exception:
        pass
    msg = await callback.message.answer(
            "<b>Введите @username нового канала:</b>\n\n<blockquote>Например @mychannel</blockquote>",
            parse_mode="HTML",
            reply_markup=AuxiliaryKeyboards.cancel_keyboard()
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

        msgd = await message.answer("<b>❌ Отмена замены канала</b>", parse_mode="HTML", reply_markup=None )
        await asyncio.sleep(1.5)
        try:
            await bot.delete_message(chat_id=msgd.chat.id, message_id=msgd.message_id)
        except Exception:
            pass

        await state.clear()

        await message.answer(
            "<b>Ваши каналы 👇</b>",
            parse_mode="HTML",
            reply_markup=StartKeyboard.get_channels_keyboard(
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

    # Получаем чат и права
    try:
        chat = await bot.get_chat(username)
        try:
            member = await bot.get_chat_member(chat.id, bot.id)
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
    if current_channel.channel_id == chat.id:
        msg = await message.answer(
            "<b>⚠️ Вы не можете заменить канал на идентичный</b>\n<blockquote>Введите @username нового канала</blockquote>",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Проверка: канал уже есть в списке
    if any(c.channel_id == chat.id for c in user_channels):
        msg = await message.answer(
            "<b>⚠️ Этот канал уже подключён в вашем списке!</b>\n\n<blockquote>Введите @username нового канала</blockquote>",
            parse_mode="HTML"
        )
        msg_ids.append(msg.message_id)
        await state.update_data(messages_to_delete=msg_ids)
        return

    # Замена канала
    current_channel.channel_id = chat.id
    current_channel.title = chat.title
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

    # Обновляем список каналов
    user_channels = await channels.get_user_channels(user.tg_id)
    can_add_channel = await channels.can_add(user.tg_id, user.perm)
    keyboard_msg = await message.answer(
        "<b>Ваши каналы 👇</b>",
        parse_mode="HTML",
        reply_markup=StartKeyboard.get_channels_keyboard(user_channels, can_add_channel)
    )
    msg_ids.append(keyboard_msg.message_id)
    

    # --- Очистка FSM ---
    await state.clear()

# Удалить канал
# =============================================
@router.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_channel_callback(callback: CallbackQuery, session, bot: Bot):
    try:
        channel_id = int(callback.data.split("_")[1])
    except ValueError:
        await callback.answer("Неверные данные", show_alert=True)
        return

    channels = Channels(session)
    user_channels = await channels.get_user_channels(callback.from_user.id)
    channel = next((ch for ch in user_channels if ch.channel_id == channel_id), None)

    if not channel:
        await callback.answer("Канал не найден", show_alert=True)
        return

    # Клавиатура подтверждения
    keyboard = StartKeyboard.confirm_delete_keyboard(channel)
    await callback.message.edit_text(
        f"<b>Вы уверены, что хотите удалить канал:</b> {channel.title}?",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()

# Подтверждение
@router.callback_query(lambda c: c.data.startswith("delete-confirm_"))
async def delete_confirm_callback(callback: CallbackQuery, session, bot: Bot):
    user_answer = bool(int(callback.data.split('_')[1][:1]))
    channel_id = int(callback.data.split('_')[1][1:])

    channels = Channels(session)
    users = Users(session)

    # Получаем пользователя
    user = await users.get_by_tg_id(callback.from_user.id)

    # Получаем канал пользователя
    user_channels = await channels.get_user_channels(user.tg_id)
    channel = next(
        (c for c in user_channels if int(c.channel_id) == channel_id),
        None
    )

    if not channel:
        return await callback.answer("⚠️ Канал не найден", show_alert=True)

    # ============================
    # Пользователь подтвердил удаление
    if user_answer:
        channel.enabled = False
        await session.commit()

        print(
            f"{Fore.RED}[CHANNEL DELETED]{Style.RESET_ALL} "
            f"id={channel.channel_id}, user={callback.from_user.id}"
        )

        await callback.answer("🗑 Канал удалён")

        # Обновляем список каналов
        user_channels = await channels.get_user_channels(user.tg_id)
        can_add_channel = await channels.can_add(user.tg_id, user.perm)

        keyboard = StartKeyboard.get_channels_keyboard(
            user_channels,
            can_add_channel
        )

        await callback.message.edit_text(
            "<b>Ваши каналы 👇</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # ============================
    # Пользователь ОТМЕНИЛ удаление
    else:
        text = (
            f"<b><blockquote>{channel.title}</blockquote></b>\n\n"
            f"<b>ID канала:</b> <code>{channel.channel_id}</code>\n"
            f"<b>Права на публикацию:</b> "
            f"{'✅' if channel.can_post else '❌'}\n"
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=StartKeyboard.channel_actions(channel.channel_id)
        )