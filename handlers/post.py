# post | Модуль для работы с постами | Rasvet Post Bot
import asyncio

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo, InputMediaAnimation, InputMediaAudio, InputMediaDocument, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.database.queries import Channels
from app.states.channel import PostStates
from app.keyboards import AuxiliaryKeyboards, ChannelKeyboards, PostKeyboards
from app.messages import BotMsg


router = Router()


# Поддерживаемый контент
# =============================================
def extract_post_data(message: Message) -> dict:

    return {
        "type": message.content_type,
        "media_group_id": message.media_group_id,
        "text": message.text,
        "caption": message.caption,
        "entities": message.entities,
        "caption_entities": message.caption_entities,
        "file_id": (
            message.photo[-1].file_id if message.photo else
            message.video.file_id if message.video else
            message.animation.file_id if message.animation else
            message.audio.file_id if message.audio else
            message.voice.file_id if message.voice else
            message.video_note.file_id if message.video_note else
            message.document.file_id if message.document else
            None
        )
    }


# Сдвиг форматирования
# =============================================
def shift_entities(entities: list, shift: int):

    if not entities:
        return []

    return [
        {
            **e,
            "offset": e["offset"] + shift
        }
        for e in entities
    ]

# Ожидания поста
# =============================================
@router.callback_query(lambda c: c.data.startswith("post_main_"))
async def post_main(callback: CallbackQuery, state: FSMContext, session):

    channel_id = int(callback.data.split("_")[-1])
    channels = Channels(session)

    channel = next(
        (ch for ch in await channels.get_user_channels(callback.from_user.id) if int(ch.channel_id) == channel_id),
        None
    )

    # Перепроверка прав публикации
    if not channel.can_post:
        return await callback.message.answer(
            BotMsg.Post.no_rights,
            parse_mode="HTML",
            reply_markup=ChannelKeyboards.invite_bot()
        )

    # Скрываем меню
    try:
        await callback.message.delete()
    except:
        pass

    msg = await callback.message.answer(
        BotMsg.Post.send,
        parse_mode="HTML",
        reply_markup=AuxiliaryKeyboards.cancel() 
    )

    await callback.answer()

    await state.set_state(PostStates.waiting_for_post)

    await state.update_data(
        channel_data=channel,
        messages_to_delete=[msg.message_id],
        posting=False,
        media_group=[]
    )


# Рання отмена
# =============================================
@router.message(PostStates.waiting_for_post, F.text == "✖️ Отменить")
async def cancel_via_reply(message: Message, state: FSMContext):

    data = await state.get_data()
    channel = data.get("channel_data")
    
    # Возвращаем меню
    await message.answer(
        BotMsg.Channel.menu(channel),
        parse_mode="HTML",
        reply_markup=ChannelKeyboards.menu(channel.channel_id)
    )

    msg = await message.answer(
        BotMsg.Post.cancel,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

    # Очистка
    for msg_id in data.get("messages_to_delete", []):
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=msg_id
            )
        except:
            pass

    try:
        await message.delete()
    except:
        pass

    await state.clear()

    await asyncio.sleep(3)
    try:
        await msg.delete()
    except:
        pass


# Превью поста
# =============================================
@router.message(PostStates.waiting_for_post)
async def handle_post(message: Message, state: FSMContext, bot: Bot):

    # Пользователь передумал отправлять пост
    if message.text == "✖️ Отменить":
        return

    data = await state.get_data()

    if data.get("posting"):
        return

    msgs = data.get("messages_to_delete", [])
    msgs.append(message.message_id)

    post = extract_post_data(message)

    # Медиа-группа
    if post.get("media_group_id"):
        media_group = data.get("media_group", [])
        media_group.append(post)

        await state.update_data(
            media_group=media_group,
            messages_to_delete=msgs
        )

        await asyncio.sleep(0.5)

        data = await state.get_data()
        media_group = data.get("media_group", [])

        if len(media_group) > 1 and media_group[-1]["file_id"] != post["file_id"]:
            return

        post = {
            "type": "media_group",
            "items": media_group
        }

    # =============================================

    await state.update_data(
        post_data=post,
        messages_to_delete=msgs
    )

    prefix = "\n\n"
    text = "Аянами Рей на каждый день"

    caption_add = prefix + text

    blockquote_offset = len(prefix)
    blockquote_length = len(text)

    caption_add_entities = [
        {
            "type": "blockquote",
            "offset": blockquote_offset,
            "length": blockquote_length
        },
        {
            "type": "text_link",
            "offset": blockquote_offset,
            "length": blockquote_length,
            "url": "https://t.me/ayanami_rei_everday"
        }
    ]

    # Превью
    preview_msg = await send_post(
        bot=bot,
        target_id=message.chat.id,
        post=post,
        caption_add=caption_add,
        caption_add_entities=caption_add_entities,
        reply_markup=None,
    )

    # Прокладка
    control_msg = await message.answer(
        BotMsg.Post.pad,
        reply_markup=PostKeyboards.confirm()
    )

    msgs.append(control_msg.message_id)

    await state.update_data(control_message_id=control_msg.message_id)

    if isinstance(preview_msg, list):
        for m in preview_msg:
            msgs.append(m.message_id)
    else:
        msgs.append(preview_msg.message_id)

    await state.update_data(messages_to_delete=msgs)
    await state.set_state(PostStates.confirm_post)


# Подтверждение поста
# =============================================
@router.callback_query(lambda c: c.data == "post_confirm", PostStates.confirm_post)
async def confirm_post(callback: CallbackQuery, state: FSMContext, bot: Bot):

    data = await state.get_data()
    channel = data.get("channel_data")

    if data.get("posting"):
        return await callback.answer("Уже публикуется", show_alert=True)

    await state.update_data(posting=True)

    await callback.answer("Публикую...")

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    channel_id = channel.channel_id
    post = data["post_data"]

    # caption_add (entity-based)
    prefix = "\n\n"
    text = "Аянами Рей на каждый день"

    caption_add = prefix + text

    blockquote_offset = len(prefix)
    blockquote_length = len(text)

    caption_add_entities = [
        {
            "type": "blockquote",
            "offset": blockquote_offset,
            "length": blockquote_length
        },

        {
            "type": "text_link",
            "offset": blockquote_offset,
            "length": blockquote_length,
            "url": "https://t.me/ayanami_rei_everday"
        }
    ]

    sent_msg = await send_post(
        bot=bot,
        target_id=channel_id,
        post=post,
        caption_add=caption_add,
        caption_add_entities=caption_add_entities
    )

    await cleanup(callback, state)

    chat_id_str = str(channel_id).replace("-100", "")

    if isinstance(sent_msg, list):
        message_id = sent_msg[0].message_id
    else:
        message_id = sent_msg.message_id

    post_link = f"https://t.me/c/{chat_id_str}/{message_id}"

    await callback.message.answer(
        BotMsg.Post.successfully_send(post_link, channel),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.message.answer(
        BotMsg.Channel.menu(channel),
        parse_mode="HTML",
        reply_markup=ChannelKeyboards.menu(channel.channel_id)
    )


# Форматирование и отправка поста
# =============================================
async def send_post(
    bot: Bot,
    target_id: int,
    post: dict,
    caption_add: str = "",
    caption_add_entities: list | None = None,
    reply_markup=None,
    disable_preview: bool = True,
):

    caption_add_entities = caption_add_entities or []

    # Медиа-группа
    if post["type"] == "media_group":

        media = []

        for i, item in enumerate(post["items"]):

            base_caption = item.get("caption") or ""
            caption = base_caption

            entities = item.get("caption_entities") or []

            if i == 0:
                caption += caption_add

                entities = entities + shift_entities(
                    caption_add_entities,
                    shift=len(base_caption)
                )

            if item["type"] == "photo":
                media.append(InputMediaPhoto(
                    media=item["file_id"],
                    caption=caption,
                    caption_entities=entities
                ))

            elif item["type"] == "video":
                media.append(InputMediaVideo(
                    media=item["file_id"],
                    caption=caption,
                    caption_entities=entities
                ))

            elif item["type"] == "animation":
                media.append(InputMediaAnimation(
                    media=item["file_id"],
                    caption=caption,
                    caption_entities=entities
                ))

            elif item["type"] == "audio":
                media.append(InputMediaAudio(
                    media=item["file_id"],
                    caption=caption,
                    caption_entities=entities
                ))

            elif item["type"] == "document":
                media.append(InputMediaDocument(
                    media=item["file_id"],
                    caption=caption,
                    caption_entities=entities
                ))

        return await bot.send_media_group(
            chat_id=target_id,
            media=media
        )

    # Текст
    if post["type"] == "text":

        base_text = post.get("text") or ""
        add_text = caption_add or ""

        text = base_text + add_text

        base_entities = post.get("entities") or []

        add_entities = shift_entities(
            caption_add_entities,
            shift=len(base_text)
        )

        return await bot.send_message(
            chat_id=target_id,
            text=text,
            entities=base_entities + add_entities,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_preview
        )

    # Медиа
    base_caption = post.get("caption") or ""
    add_caption = caption_add or ""

    caption = base_caption + add_caption

    base_entities = post.get("caption_entities") or []

    add_entities = shift_entities(
        caption_add_entities,
        shift=len(base_caption)
    )

    entities = base_entities + add_entities

    if post["type"] == "photo":
        return await bot.send_photo(
            chat_id=target_id,
            photo=post["file_id"],
            caption=caption,
            caption_entities=entities,
            reply_markup=reply_markup
        )

    if post["type"] == "video":
        return await bot.send_video(
            chat_id=target_id,
            video=post["file_id"],
            caption=caption,
            caption_entities=entities,
            reply_markup=reply_markup
        )

    if post["type"] == "animation":
        return await bot.send_animation(
            chat_id=target_id,
            animation=post["file_id"],
            caption=caption,
            caption_entities=entities,
            reply_markup=reply_markup
        )

    if post["type"] == "audio":
        return await bot.send_audio(
            chat_id=target_id,
            audio=post["file_id"],
            caption=caption,
            caption_entities=entities,
            reply_markup=reply_markup
        )

    if post["type"] == "document":
        return await bot.send_document(
            chat_id=target_id,
            document=post["file_id"],
            caption=caption,
            caption_entities=entities,
            reply_markup=reply_markup
        )

    if post["type"] == "voice":
        return await bot.send_voice(
            chat_id=target_id,
            voice=post["file_id"],
            reply_markup=reply_markup
        )

    if post["type"] == "video_note":
        return await bot.send_video_note(
            chat_id=target_id,
            video_note=post["file_id"]
        )

    return await bot.send_message(
        chat_id=target_id,
        text="❌ Неподдерживаемый тип"
    )


# Поздняя отмена
# =============================================
@router.callback_query(lambda c: c.data == "post_cancel", PostStates.confirm_post)
async def cancel_post(callback: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    channel = data.get("channel_data")

    await callback.message.answer(
        BotMsg.Channel.menu(channel),
        parse_mode="HTML",
        reply_markup=ChannelKeyboards.menu(channel.channel_id)
    )

    msg = await callback.message.answer(BotMsg.Post.cancel, parse_mode="HTML")

    await cleanup(callback, state)

    await asyncio.sleep(3)

    try:
        await msg.delete()
    except:
        pass


# Очистка
# =============================================
async def cleanup(callback: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    msgs = data.get("messages_to_delete", [])

    for msg_id in msgs:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=msg_id
            )
        except:
            pass

    await state.clear()