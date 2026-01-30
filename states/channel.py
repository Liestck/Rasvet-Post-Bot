from aiogram.fsm.state import StatesGroup, State


class ChannelStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_username_replace = State()