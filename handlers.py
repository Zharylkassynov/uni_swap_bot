from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import (
    ADMIN_GROUP_ID,
    CHANNEL_ID,
    KASPI_PHONE,
    KASPI_NAME,
    PRICE,
)

from keyboards import (
    main_menu,
    categories_kb,
    admin_check_kb,
    admin_publish_kb,
    retry_ad_kb,
    retry_receipt_kb,
)

from states import AdForm

router = Router()

# ================== STORAGE ==================
# ad_id -> dict
PENDING_ADS = {}


# -------------------- START --------------------

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в UNI Swap ♻️\n\n"
        "Платформа для обмена и аренды вещей между студентами.",
        reply_markup=main_menu()
    )


# -------------------- INFO --------------------

@router.callback_query(F.data == "cats")
async def categories_handler(callback: CallbackQuery):
    await callback.message.answer(
        "📂 Категории объявлений:\n"
        "• 👕 Одежда\n"
        "• 📚 Книги\n"
        "• 💻 Электроника\n"
        "• 🏠 Для дома\n"
        "• 🎓 Учёба\n"
        "• 📦 Другое"
    )
    await callback.answer()


@router.callback_query(F.data == "rules")
async def rules_handler(callback: CallbackQuery):
    await callback.message.answer(
        "📜 Правила UNI Swap:\n\n"
        "• Обычные объявления — бесплатно\n"
        "• SOS объявления — платные\n"
        "• Фото обязательно\n"
        "• Нужен @username\n"
        "• Админ может отказать"
    )
    await callback.answer()


# -------------------- ADD AD --------------------

@router.callback_query(F.data == "add")
async def add_ad_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.photo)
    await callback.message.answer("📸 Отправьте фото вещи")
    await callback.answer()


@router.message(AdForm.photo, F.photo)
async def ad_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdForm.description)
    await message.answer("📝 Напишите описание")


@router.message(AdForm.description)
async def ad_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdForm.price)
    await message.answer("💰 Укажите цену")


@router.message(AdForm.price)
async def ad_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(AdForm.category)
    await message.answer("📂 Выберите категорию", reply_markup=categories_kb())


@router.callback_query(F.data.startswith("cat:"))
async def ad_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]
    data = await state.get_data()
    await state.clear()

    user = callback.from_user

    if not user.username:
        await callback.message.answer(
            "❌ Для публикации нужен @username.\n"
            "Добавьте его в настройках Telegram."
        )
        await callback.answer()
        return

    username = "@" + user.username

    admin_caption = (
        "🆕 Новое объявление\n\n"
        "👤 Пользователь: " + user.full_name + "\n"
        "🆔 ID: " + str(user.id) + "\n"
        "🔗 Username: " + username + "\n\n"
        "📌 Категория: " + category + "\n"
        "📝 Описание: " + data["description"] + "\n"
        "💰 Цена: " + data["price"]
    )

    public_caption = (
        "📌 " + category + "\n\n"
        "📝 " + data["description"] + "\n"
        "💰 " + data["price"] + "\n\n"
        "📩 Связь: " + username + "\n"
        "♻️ UNI Swap"
    )

    ad_id = hash((user.id, public_caption))

    PENDING_ADS[ad_id] = {
        "photo": data["photo"],
        "admin_caption": admin_caption,
        "public_caption": public_caption,
        "user_id": user.id,
    }

    await callback.bot.send_photo(
        ADMIN_GROUP_ID,
        photo=data["photo"],
        caption=admin_caption,
        reply_markup=admin_check_kb(ad_id)
    )

    await callback.message.answer("✅ Объявление отправлено на модерацию")
    await callback.answer()


# -------------------- ADMIN APPROVE --------------------

@router.callback_query(F.data.startswith("admin:approved:"))
async def admin_approved(callback: CallbackQuery):
    ad_id = int(callback.data.split(":")[2])
    ad = PENDING_ADS.get(ad_id)

    if not ad:
        await callback.answer("Не найдено", show_alert=True)
        return

    text = (
        "✅ Объявление одобрено\n\n"
        "💳 Для SOS объявления оплатите " + str(PRICE) + " тг\n"
        "📱 " + KASPI_PHONE + "\n"
        "👤 " + KASPI_NAME + "\n\n"
        "📎 Отправьте чек (PDF или фото)"
    )

    await callback.bot.send_message(ad["user_id"], text)
    await callback.message.answer("⏳ Ожидаем чек")
    await callback.answer()


# -------------------- USER RECEIPT --------------------

@router.message(F.photo | F.document)
async def receipt_handler(message: Message):
    ads = [
        (ad_id, ad)
        for ad_id, ad in PENDING_ADS.items()
        if ad["user_id"] == message.from_user.id
    ]

    if not ads:
        return

    ad_id, _ = ads[0]

    user = message.from_user
    username = "@" + user.username if user.username else "—"

    caption = (
        "💳 Чек оплаты\n\n"
        "👤 " + user.full_name + "\n"
        "🔗 " + username + "\n"
        "🆔 " + str(user.id)
    )

    if message.photo:
        await message.bot.send_photo(
            ADMIN_GROUP_ID,
            photo=message.photo[-1].file_id,
            caption=caption,
            reply_markup=admin_publish_kb(ad_id)
        )
    else:
        await message.bot.send_document(
            ADMIN_GROUP_ID,
            document=message.document.file_id,
            caption=caption,
            reply_markup=admin_publish_kb(ad_id)
        )

    await message.answer("📎 Чек получен")


# -------------------- ADMIN PUBLISH --------------------

@router.callback_query(F.data.startswith("admin:publish:"))
async def admin_publish(callback: CallbackQuery):
    ad_id = int(callback.data.split(":")[2])
    ad = PENDING_ADS.get(ad_id)

    if not ad:
        await callback.answer("Не найдено", show_alert=True)
        return

    await callback.bot.send_photo(
        CHANNEL_ID,
        photo=ad["photo"],
        caption=ad["public_caption"]
    )

    await callback.bot.send_message(
        ad["user_id"],
        "🎉 Ваше объявление опубликовано!"
    )

    del PENDING_ADS[ad_id]

    await callback.message.answer("✅ Опубликовано")
    await callback.answer()


# -------------------- ADMIN REJECT --------------------

@router.callback_query(F.data.startswith("admin:reject:"))
async def admin_reject(callback: CallbackQuery):
    ad_id = int(callback.data.split(":")[2])
    ad = PENDING_ADS.get(ad_id)

    if not ad:
        await callback.answer("Не найдено", show_alert=True)
        return

    caption = callback.message.caption or ""
    is_receipt = "Чек оплаты" in caption

    if is_receipt:
        await callback.bot.send_message(
            ad["user_id"],
            "❌ Чек отклонён.\n"
            "Отправьте чек ещё раз.",
            reply_markup=retry_receipt_kb()
        )
    else:
        await callback.bot.send_message(
            ad["user_id"],
            "❌ Объявление отклонено.",
            reply_markup=retry_ad_kb()
        )
        del PENDING_ADS[ad_id]

    await callback.message.answer("❌ Отклонено")
    await callback.answer()


@router.callback_query(F.data == "retry_receipt")
async def retry_receipt(callback: CallbackQuery):
    await callback.message.answer("📎 Отправьте чек (PDF или фото)")
    await callback.answer()
