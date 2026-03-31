# keyboards | Помодульные неймспейсы клавиатур | Rasvet Post Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Channel


class ChannelKeyboards:
    """ Клавиатуры для взаимодействия с каналами """

    @staticmethod
    def menu(channel_id) -> InlineKeyboardMarkup:
        """ Управление каналом """
        inline_keyboard = [
            [InlineKeyboardButton(text="📢 Публикация", callback_data=f"post_main_{channel_id}") ],
            [InlineKeyboardButton(text="📬 Предложка", callback_data=f"suggest_main") ],
            [InlineKeyboardButton(text="⚙️ Формат постов", callback_data=f"post_format_main") ],
            [
                InlineKeyboardButton(text="✏️", callback_data=f"edit_{channel_id}"),
                InlineKeyboardButton(text="🗑", callback_data=f"delete_{channel_id}") 
            ],
            [InlineKeyboardButton(text="⬅️ Список каналов", callback_data=f"channels_main") ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @staticmethod
    def _list(channels: list[Channel], can_add_channel: bool) -> InlineKeyboardMarkup:
        """
        Формирует клавиатуру со списком каналов и кнопкой добавления.

        :param channels: список Channel
        :param can_add_channel: можно ли добавлять канал (лимит)
        """
        channels_list = []

        for ch in channels:
            channels_list.append([
                InlineKeyboardButton(text=f'{ch.title}', callback_data=f"view_{ch.channel_id}"),
            ])

        # Добавить канал
        if can_add_channel:
            channels_list.append([
                InlineKeyboardButton(text="➕ Подключить канал", callback_data="add_channel")
            ])

        # Ограничение
        else:
            channels_list.append([
                InlineKeyboardButton(text="🚫 Достигнут лимит каналов", callback_data="cannot_add")
            ])

        return InlineKeyboardMarkup(inline_keyboard=channels_list)

    @staticmethod
    def invite_bot() -> InlineKeyboardMarkup:
        """ Добавления бота в канал и выдача прав """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Добавить бота в канал", url="https://t.me/RasvetPost_bot?startchannel=1")] 
        ])
    
    @staticmethod
    def confirm_delete(channel: Channel) -> InlineKeyboardMarkup:
        """ Клавиатура подтверждения удаления канала """
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"delete-confirm_1{channel.channel_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"delete-confirm_0{channel.channel_id}")
            ]
        ])


class PostKeyboards:
    """ Клавиатуры модуля << Публикация >> """

    @staticmethod
    def confirm() -> InlineKeyboardMarkup:
        """ Подтверждение отправки поста """
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Запостить", callback_data="post_confirm")],
            [InlineKeyboardButton(text="✖️ Отмена", callback_data="post_cancel")]
        ])


class AuxiliaryKeyboards:
    """ Вспомогательные клавиатуры """

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✖️ Отменить")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )