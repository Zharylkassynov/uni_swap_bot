from aiogram.fsm.state import StatesGroup, State

class AdForm(StatesGroup):
    photo = State()
    description = State()
    price = State()
    category = State()
    preview = State()
    wait_moderation = State()
    wait_payment = State()
    wait_receipt = State()
