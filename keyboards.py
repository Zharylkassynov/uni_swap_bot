from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Подать объявление", callback_data="add")],
        [InlineKeyboardButton(text="📂 Категории", callback_data="cats")],
        [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
        [InlineKeyboardButton(text="📞 Связаться с админом", url="https://t.me/nelyashakh")]
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

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

def ad_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Обычное (бесплатно)", callback_data="type:normal")
        ],
        [
            InlineKeyboardButton(text="🚨 SOS (500 тг)", callback_data="type:sos")
        ]
    ])
