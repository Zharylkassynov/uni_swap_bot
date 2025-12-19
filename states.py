from aiogram.fsm.state import StatesGroup, State

class AdForm(StatesGroup):
    ad_type = State()  # Выбор типа объявления (regular/sos)
    photo = State()
    description = State()
    price = State()
    category = State()
    preview = State()
    wait_moderation = State()
    wait_payment = State()
    wait_receipt = State()
    sos_description = State()  # Описание для SOS объявлений
