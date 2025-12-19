from aiogram.fsm.state import StatesGroup, State


class AdForm(StatesGroup):
    photo = State()
    description = State()
    price = State()
    category = State()
