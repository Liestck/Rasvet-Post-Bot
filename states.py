# states | Rasvet Post Bot
from aiogram.fsm.state import StatesGroup, State


# Каналы
class ChannelStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_username_replace = State()


# Публикация
class PostStates(StatesGroup):
    waiting_for_post = State()
    confirm_post = State()


# Формат постов
class FormatStates(StatesGroup):
    menu = State()
    editing = State()


# Предложка
class SuggestStates(StatesGroup):
    waiting_for_token = State()