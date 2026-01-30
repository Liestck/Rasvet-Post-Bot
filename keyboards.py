from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Channel

class StartKeyboard:
    """Клавиатура для /start — список каналов и кнопка +"""

    @staticmethod
    def get_channels_keyboard(channels: list[Channel], can_add_channel: bool) -> InlineKeyboardMarkup:
        """
        Формирует клавиатуру со списком каналов и кнопкой добавления.

        :param channels: список Channel
        :param can_add_channel: можно ли добавлять канал (лимит)
        """
        inline_keyboard = []

        for ch in channels:
            inline_keyboard.append([
                InlineKeyboardButton(text=f'{ch.title}', callback_data=f"view_{ch.channel_id}"),
                #InlineKeyboardButton(text="✏️", callback_data=f"edit_{ch.channel_id}"),
                #InlineKeyboardButton(text="🗑", callback_data=f"delete_{ch.channel_id}")
            ])

        # Кнопка "+" для добавления нового канала
        if can_add_channel:
            inline_keyboard.append([
                InlineKeyboardButton(text="➕ Подключить канал", callback_data="add_channel")
            ])
        else:
            inline_keyboard.append([
                InlineKeyboardButton(text="🚫 Достигнут лимит каналов", callback_data="cannot_add")
            ])

        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @staticmethod
    def channel_actions(channel_id) -> InlineKeyboardMarkup:
        """Клавиатура для показа деталей одного канала"""
        inline_keyboard = [
            [
                InlineKeyboardButton(text="✏️", callback_data=f"edit_{channel_id}"),
                InlineKeyboardButton(text="🗑", callback_data=f"delete_{channel_id}") 
            ],
            [InlineKeyboardButton(text="⬅️ Список каналов", callback_data=f"channels_main") ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @staticmethod
    def confirm_delete_keyboard(channel: Channel) -> InlineKeyboardMarkup:
        """Клавиатура подтверждения удаления канала"""
        inline_keyboard = [
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"delete-confirm_1{channel.channel_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"delete-confirm_0{channel.channel_id}")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

class AuxiliaryKeyboards:
    def cancel_keyboard():
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✖️ Отменить")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )