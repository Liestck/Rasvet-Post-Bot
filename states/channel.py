from aiogram.fsm.state import StatesGroup, State


class ChannelStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_username_replace = State()


class PostStates(StatesGroup):
    waiting_for_post = State()
    confirm_post = State()