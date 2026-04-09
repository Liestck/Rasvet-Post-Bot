# app.handlers.suggest.main | Управление предложкой | Rasvet Post Bot
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from sqlalchemy import select

from app.database.models import Channel
from app.database.queries import Suggest
from app.states import SuggestStates
from app.keyboards import SuggestKeyboards, ChannelKeyboards
from app.messages import BotMsg
from app.config import Config
from app.handlers.suggest.manager import suggest_runner
from app.utils.crypto import crypto


router = Router()

# Сборщик текста
# =============================================
def build_suggest_text(channel, token: bool):
    return BotMsg.Suggest.menu(channel, token)


# Меню предложки
# =============================================
@router.callback_query(F.data.startswith("suggest_main_"))
async def suggest_main(callback: CallbackQuery, state: FSMContext, session):
    channel_id = int(callback.data.split("_")[-1])

    channel = await session.scalar(
        select(Channel).where(
            Channel.channel_id == channel_id,
            Channel.owner_id == callback.from_user.id
        )
    )

    if not channel:
        await callback.answer("❌ Канал не найден", show_alert=True)
        return

    await state.update_data(channel_id=channel_id)

    suggest = Suggest(session)
    token = await suggest.get_suggest_token(channel_id)

    await callback.message.edit_text(
        build_suggest_text(channel, token),
        parse_mode="HTML",
        reply_markup=SuggestKeyboards.menu(
            channel_id=channel_id,
            has_token=bool(token),
            username=channel.suggest_username
        ),
        disable_web_page_preview=True
    )

# Подключение бота
# =============================================
@router.callback_query(F.data.startswith("suggest_bind_"))
async def suggest_bind(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split("_")[-1])

    await state.update_data(channel_id=channel_id)
    await state.set_state(SuggestStates.waiting_for_token)
    

    await callback.message.edit_text(
        BotMsg.Suggest.bind_prompt,
        parse_mode="HTML",
        reply_markup=SuggestKeyboards.cancel_connect(channel_id)
    )

    await state.update_data(
        prompt_msg_id=callback.message.message_id
    )


# Чтение токена
# =============================================
@router.message(SuggestStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext, session, bot: Bot):

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    channel_id = data.get("channel_id")

    channel = await session.scalar(
        select(Channel).where(
            Channel.channel_id == channel_id,
            Channel.owner_id == message.from_user.id
        )
    )

    token = message.text.strip()
    suggest = Suggest(session)

    try:
        await message.delete()
    except:
        pass

    async def show_error(text: str):
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=prompt_msg_id,
                text=f"{BotMsg.Suggest.bind_prompt}\n\n{text}",
                parse_mode="HTML"
            )
        except:
            pass

    async def set_status(text: str):
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=prompt_msg_id,
                text=f"{BotMsg.Suggest.bind_prompt}\n\n<blockquote>⏳ {text}</blockquote>",
                parse_mode="HTML"
            )
        except:
            pass

    # =============================================
    await set_status(BotMsg.Suggest.step_format)

    if ":" not in token:
        await show_error(BotMsg.Suggest.invalid_format)
        return

    # =============================================
    await set_status(BotMsg.Suggest.step_api)

    try:
        test_bot = Bot(token=token)
        bot_info = await test_bot.get_me()
    except Exception:
        await show_error(BotMsg.Suggest.invalid_token)
        return

    # =============================================
    await set_status(BotMsg.Suggest.step_send)

    try:
        await test_bot.send_message(
            chat_id=message.from_user.id,
            text=BotMsg.Suggest.success_connected(
                bot_info.username,
                bot_info.first_name
            ),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception:
        await show_error(BotMsg.Suggest.send_fail)
        return

    await suggest.set_suggest_token(channel_id, token)
    await suggest.set_suggest_username(channel_id, bot_info.username)

    # Запуск бота
    await suggest_runner.start_bot(
        channel_id=channel_id,
        token=token
    )

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=prompt_msg_id,
        text=build_suggest_text(channel, True),
        parse_mode="HTML",
        reply_markup=SuggestKeyboards.menu(
            channel_id=channel_id,
            has_token=True,
            username=bot_info.username
        ),
        disable_web_page_preview=True
    )

    await state.clear()

# Отмена запроса токена
# =============================================
@router.callback_query(F.data.startswith("suggest_cancel_connect_"))
async def suggest_cancel_connect(callback: CallbackQuery, state: FSMContext, session):

    channel_id = int(callback.data.split("_")[-1])

    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")

    channel = await session.scalar(
        select(Channel).where(
            Channel.channel_id == channel_id,
            Channel.owner_id == callback.from_user.id
        )
    )

    await state.clear()
    await callback.answer()

    if prompt_msg_id:
        try:
            await callback.message.edit_text(
                build_suggest_text(channel, False),
                parse_mode="HTML",
                reply_markup=SuggestKeyboards.menu(
                    channel_id=channel_id,
                    has_token=bool(channel.suggest_token),
                    username=channel.suggest_username
                ),
                disable_web_page_preview=True
            )
        except:
            pass


# Отвязка бота
# =============================================
@router.callback_query(F.data.startswith("suggest_unbind_"))
async def suggest_unbind(callback: CallbackQuery, session):

    channel_id = int(callback.data.split("_")[-1])

    channel = await session.scalar(
        select(Channel).where(
            Channel.channel_id == channel_id,
            Channel.owner_id == callback.from_user.id
        )
    )

    channel.suggest_token = None
    channel.suggest_username = None

    await session.commit()

    # Остановка бота
    await suggest_runner.stop_bot(channel_id)

    await callback.message.edit_text(
        build_suggest_text(channel, False),
        parse_mode="HTML",
        reply_markup=SuggestKeyboards.menu(
            channel_id=channel_id,
            has_token=False,
            username=None
        )
    )

    await callback.answer()


# Возваращение в меню
# =============================================
@router.callback_query(F.data.startswith("suggest_return_"))
async def suggest_return(callback: CallbackQuery, session):

    channel_id = int(callback.data.split("_")[-1])

    channel = await session.scalar(
        select(Channel).where(
            Channel.channel_id == channel_id,
            Channel.owner_id == callback.from_user.id
        )
    )

    await callback.message.edit_text(
        BotMsg.Channel.menu(channel),
        parse_mode="HTML",
        reply_markup=ChannelKeyboards.menu(channel.channel_id),
        disable_web_page_preview=True
    )

    await callback.answer()