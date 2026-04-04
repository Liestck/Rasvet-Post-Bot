from aiogram.fsm.state import StatesGroup, State

class FormatStates(StatesGroup):
    menu = State()
    editing = State()