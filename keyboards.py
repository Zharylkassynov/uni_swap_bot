from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Подать объявление", callback_data="add")],
        [InlineKeyboardButton(text="📂 Категории", callback_data="cats")],
        [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
        [InlineKeyboardButton(text="📞 Связаться с админом", url="https://t.me/nelyashakh")]
    ])

def ad_type_kb():
    """Клавиатура выбора типа объявления"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🆓 Обычное объявление (бесплатно)",
                callback_data="ad_type:regular"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚨 SOS объявление (500 тг)",
                callback_data="ad_type:sos"
            )
        ]
    ])

def categories_kb():
    buttons = [
        "👕 Одежда", "📚 Книги", "💻 Электроника",
        "🏠 Для дома", "🎓 Учёба", "📦 Другое"
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=b, callback_data=f"cat:{b}")]
        for b in buttons
    ])

def admin_check_kb(ad_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Проверено",
                callback_data=f"admin:approved:{ad_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"admin:reject:{ad_id}"
            ),
        ]
    ])


def admin_publish_kb(ad_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Опубликовать",
                callback_data=f"admin:publish:{ad_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"admin:reject:{ad_id}"
            ),
        ]
    ])


def retry_ad_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔁 Подать объявление заново",
                callback_data="add"
            )
        ]
    ])


def retry_receipt_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📎 Отправить чек ещё раз",
                callback_data="retry_receipt"
            )
        ]
    ])


def main_reply_menu():
    """Постоянное меню внизу чата (ReplyKeyboardMarkup)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Подать объявление"),
                KeyboardButton(text="📂 Категории")
            ],
            [
                KeyboardButton(text="📜 Правила"),
                KeyboardButton(text="📞 Связь с админом")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
