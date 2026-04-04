# post | Модуль для работы с постами | Rasvet Post Bot
import asyncio

from aiogram import Router, Bot, F
from aiogram.types import (
    CallbackQuery, Message,
    InputMediaPhoto, InputMediaVideo,
    InputMediaAnimation, InputMediaAudio,
    InputMediaDocument, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext

from app.database.queries import Channels, Format
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


# Ожидания поста
# =============================================
@router.callback_query(lambda c: c.data.startswith("post_main_"))
async def post_main(callback: CallbackQuery, state: FSMContext, session):

    channel_id = int(callback.data.split("_")[-1])
    channels = Channels(session)

    channel = next((ch for ch in await channels.get_user_channels(callback.from_user.id)if int(ch.channel_id) == channel_id), None)

    if not channel.can_post:
        return await callback.message.answer(
            BotMsg.Post.no_rights,
            parse_mode="HTML",
            reply_markup=ChannelKeyboards.invite_bot()
        )

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
        session=session,
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

    await state.update_data(
        post_data=post,
        messages_to_delete=msgs
    )

    preview_msg = await send_post(
        bot=bot,
        state=state,
        target_id=message.chat.id,
        post=post,
        reply_markup=None
    )

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

    post = data["post_data"]

    sent_msg = await send_post(
        bot=bot,
        state=state,
        target_id=channel.channel_id,
        post=post
    )

    await cleanup(callback, state)

    chat_id_str = str(channel.channel_id).replace("-100", "")

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
    state: FSMContext,
    target_id: int,
    post: dict,
    reply_markup=None,
    disable_preview: bool = True,
):

    data = await state.get_data()
    session = data.get("session")

    up_text, down_text = "", ""

    if session:
        fmt = Format(session)
        up_text, down_text = await fmt.get_texts(
            owner_tg_id=data["channel_data"].owner_id,
            channel_id=data["channel_data"].channel_id
        )

    up_text = up_text or ""
    down_text = down_text or ""

    # MEDIA GROUP
    if post["type"] == "media_group":

        media = []

        for i, item in enumerate(post["items"]):

            caption_parts = []

            if i == 0 and up_text:
                caption_parts.append(up_text)

            base_caption = item.get("caption") or ""
            caption_parts.append(base_caption)

            if i == 0 and down_text:
                caption_parts.append(down_text)

            caption = "\n\n".join([c for c in caption_parts if c])

            media_kwargs = {
                "media": item["file_id"],
                "caption": caption if caption else None,
            }

            if item["type"] == "photo":
                media.append(InputMediaPhoto(**media_kwargs))
            elif item["type"] == "video":
                media.append(InputMediaVideo(**media_kwargs))
            elif item["type"] == "animation":
                media.append(InputMediaAnimation(**media_kwargs))
            elif item["type"] == "audio":
                media.append(InputMediaAudio(**media_kwargs))
            elif item["type"] == "document":
                media.append(InputMediaDocument(**media_kwargs))

        return await bot.send_media_group(
            chat_id=target_id,
            media=media
        )
    
    # TEXT
    if post["type"] == "text":

        parts = []

        if up_text:
            parts.append(up_text)

        if post.get("text"):
            parts.append(post["text"])

        if down_text:
            parts.append(down_text)

        text = "\n\n".join(parts)

        return await bot.send_message(
            chat_id=target_id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
            disable_web_page_preview=disable_preview
        )

    # =============================================
    # MEDIA (single)
    # =============================================
    base_caption = post.get("caption") or ""

    parts = []

    if up_text:
        parts.append(up_text)

    if base_caption:
        parts.append(base_caption)

    if down_text:
        parts.append(down_text)

    caption = "\n\n".join(parts)

    kwargs = {
        "chat_id": target_id,
        "caption": caption if caption else None,
        "reply_markup": reply_markup,
        "parse_mode": "HTML"
    }

    if post["type"] == "photo":
        return await bot.send_photo(photo=post["file_id"], **kwargs)

    if post["type"] == "video":
        return await bot.send_video(video=post["file_id"], **kwargs)

    if post["type"] == "animation":
        return await bot.send_animation(animation=post["file_id"], **kwargs)

    if post["type"] == "audio":
        return await bot.send_audio(audio=post["file_id"], **kwargs)

    if post["type"] == "document":
        return await bot.send_document(document=post["file_id"], **kwargs)

    if post["type"] == "voice":
        return await bot.send_voice(
            chat_id=target_id,
            voice=post["file_id"]
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