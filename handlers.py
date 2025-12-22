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
    SOS_PRICE,
)

from keyboards import (
    main_menu,
    categories_kb,
    admin_check_kb,
    admin_publish_kb,
    retry_ad_kb,
    retry_receipt_kb,
    ad_type_kb,
    main_reply_menu,
)


from states import AdForm

router = Router()

# ================== ХРАНИЛИЩЕ ЗАЯВОК ==================
# ad_id -> {type: "regular"|"sos", photo (None для SOS), admin_caption, public_caption, user_id}
PENDING_ADS = {}


# -------------------- START --------------------

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Добро пожаловать в UNI Swap ♻️\n\n"
        "Платформа для обмена и аренды вещей между студентами.",
        reply_markup=main_reply_menu()
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
        "• 📦 Другое",
        reply_markup=main_reply_menu()
    )
    await callback.answer()


@router.message(F.text == "📂 Категории")
async def categories_text_handler(message: Message, state: FSMContext):
    """Обработчик текстовой кнопки 'Категории'"""
    await state.clear()  # Очищаем состояние FSM, если было активно
    await message.answer(
        "📂 Категории объявлений:\n"
        "• 👕 Одежда\n"
        "• 📚 Книги\n"
        "• 💻 Электроника\n"
        "• 🏠 Для дома\n"
        "• 🎓 Учёба\n"
        "• 📦 Другое",
        reply_markup=main_reply_menu()
    )


@router.callback_query(F.data == "rules")
async def rules_handler(callback: CallbackQuery):
    await callback.message.answer(
        "📜 Правила UNI Swap:\n\n"
        "• Обычное объявление — бесплатно\n"
        "• SOS объявление — 500 тг\n"
        "• Фото обязательно (только для обычных объявлений)\n"
        "• Для публикации нужен @username\n"
        "• Один товар — одно объявление\n"
        "• Админ может отказать в публикации",
        reply_markup=main_reply_menu()
    )
    await callback.answer()


@router.message(F.text == "📜 Правила")
async def rules_text_handler(message: Message, state: FSMContext):
    """Обработчик текстовой кнопки 'Правила'"""
    await state.clear()  # Очищаем состояние FSM, если было активно
    await message.answer(
        "📜 Правила UNI Swap:\n\n"
        "• Обычное объявление — бесплатно\n"
        "• SOS объявление — 500 тг\n"
        "• Фото обязательно (только для обычных объявлений)\n"
        "• Для публикации нужен @username\n"
        "• Один товар — одно объявление\n"
        "• Админ может отказать в публикации",
        reply_markup=main_reply_menu()
    )


# -------------------- ADD AD (FSM) --------------------

@router.callback_query(F.data == "add")
async def add_ad_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdForm.ad_type)
    await callback.message.answer(
        "📝 Выберите тип объявления:",
        reply_markup=ad_type_kb()
    )
    await callback.answer()


@router.message(F.text == "➕ Подать объявление")
async def add_ad_text_handler(message: Message, state: FSMContext):
    """Обработчик текстовой кнопки 'Подать объявление'"""
    await state.clear()  # Очищаем предыдущее состояние, если было
    await state.set_state(AdForm.ad_type)
    await message.answer(
        "📝 Выберите тип объявления:",
        reply_markup=ad_type_kb()
    )


@router.callback_query(F.data.startswith("ad_type:"))
async def ad_type_selected(callback: CallbackQuery, state: FSMContext):
    ad_type = callback.data.split(":")[1]  # "regular" или "sos"
    await state.update_data(ad_type=ad_type)
    
    if ad_type == "sos":
        # SOS объявления: только описание
        await state.set_state(AdForm.sos_description)
        await callback.message.answer(
            "🆘 Опишите, что вам срочно нужно.(500 тг)\n\n"
            "Пример:\n"
            "— Срочно нужен калькулятор Casio на сегодня\n"
            "— Нужен учебник по математике до завтра"
        )
    else:
        # Обычные объявления: фото, описание, цена, категория
        await state.set_state(AdForm.photo)
        await callback.message.answer("📸 Отправьте фото вещи")
    
    await callback.answer()


@router.message(AdForm.photo, F.photo)
async def ad_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AdForm.description)
    await message.answer("📝 Напишите описание вещи")


@router.message(AdForm.sos_description)
async def sos_description_handler(message: Message, state: FSMContext):
    """Обработчик описания для SOS объявлений"""
    description = message.text
    if not description or not description.strip():
        await message.answer(
            "❌ Пожалуйста, отправьте текстовое описание.",
            reply_markup=main_reply_menu()
        )
        return
    
    data = await state.get_data()
    await state.clear()
    
    user = message.from_user
    ad_type = data.get("ad_type", "sos")
    
    # ❗️username ОБЯЗАТЕЛЕН для публикации
    if not user.username:
        await message.answer(
            "❌ Для публикации объявления у вас должен быть установлен @username.\n"
            "Пожалуйста, добавьте username в настройках Telegram и попробуйте снова.",
            reply_markup=main_reply_menu()
        )
        return
    
    username = f"@{user.username}"
    
    # Формируем admin_caption для SOS объявления
    admin_caption = (
        "🆘 SOS ОБЪЯВЛЕНИЕ\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"📝 Описание: {description}"
    )
    
    # Формируем public_caption для SOS объявления
    public_caption = (
        "🆘 SOS ОБЪЯВЛЕНИЕ 🆘\n\n"
        f"📝 {description}\n\n"
        f"📩 Связь: {username}\n"
        "♻️ UNI Swap"
    )
    
    ad_id = hash((user.id, public_caption, ad_type))
    
    PENDING_ADS[ad_id] = {
        "type": ad_type,
        "photo": None,  # SOS объявления без фото
        "admin_caption": admin_caption,
        "public_caption": public_caption,
        "user_id": user.id,
    }
    
    # Отправляем в админ-группу без фото (только текст)
    await message.bot.send_message(
        ADMIN_GROUP_ID,
        text=admin_caption,
        reply_markup=admin_publish_kb(ad_id)
    )
    
    await message.answer(
        "✅ Объявление отправлено на проверку модератору.\n"
        "⏳ Ожидайте ответа.",
        reply_markup=main_reply_menu()
    )


@router.message(AdForm.description)
async def ad_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AdForm.price)
    await message.answer("💰 Укажите цену или условия аренды")


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
    ad_type = data.get("ad_type", "regular")  # По умолчанию regular

    # ❗️username ОБЯЗАТЕЛЕН для публикации
    if not user.username:
        await callback.message.answer(
            "❌ Для публикации объявления у вас должен быть установлен @username.\n"
            "Пожалуйста, добавьте username в настройках Telegram и попробуйте снова.",
            reply_markup=main_reply_menu()
        )
        await callback.answer()
        return

    username = f"@{user.username}"

    # Формируем admin_caption для обычного объявления
    admin_caption = (
        "🆕 ОБЫЧНОЕ ОБЪЯВЛЕНИЕ\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"📌 Категория: {category}\n"
        f"📝 Описание: {data['description']}\n"
        f"💰 Цена: {data['price']}"
    )

    # Формируем public_caption для обычного объявления
    public_caption = (
        f"📌 {category}\n\n"
        f"📝 {data['description']}\n"
        f"💰 {data['price']}\n\n"
        f"📩 Связь: {username}\n"
        "♻️ UNI Swap"
    )

    ad_id = hash((user.id, public_caption, ad_type))

    PENDING_ADS[ad_id] = {
        "type": ad_type,
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

    await callback.message.answer(
        "✅ Объявление отправлено на проверку модератору.\n"
        "⏳ Ожидайте ответа.",
        reply_markup=main_reply_menu()
    )
    await callback.answer()


# -------------------- ADMIN: APPROVE --------------------

@router.callback_query(F.data.startswith("admin:approved:"))
async def admin_approved(callback: CallbackQuery):
    ad_id = int(callback.data.split(":")[2])
    ad = PENDING_ADS.get(ad_id)

    if not ad:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    ad_type = ad.get("type", "regular")

    if ad_type == "regular":
        # Обычное объявление публикуется сразу после одобрения
        await callback.bot.send_photo(
            CHANNEL_ID,
            photo=ad["photo"],
            caption=ad["public_caption"]
        )

        await callback.bot.send_message(
            ad["user_id"],
            "🎉 Ваше объявление опубликовано в канале UNI Swap!\n"
            "Спасибо за использование платформы ♻️",
            reply_markup=main_reply_menu()
        )

        del PENDING_ADS[ad_id]
        await callback.message.answer("✅ Объявление опубликовано")
        await callback.answer()
    else:
        # SOS объявление требует оплаты
        await callback.bot.send_message(
            ad["user_id"],
            "✅ Ваше SOS объявление прошло проверку.\n\n"
            f"💳 Для публикации переведите {SOS_PRICE} тг через Kaspi:\n"
            f"📱 {KASPI_PHONE}\n"
            f"👤 {KASPI_NAME}\n\n"
            "📎 После оплаты отправьте ЧЕК (PDF или фото) в этот чат.",
            reply_markup=main_reply_menu()
        )

        await callback.message.answer("⏳ Ожидаем чек от пользователя")
        await callback.answer()


# -------------------- USER: SEND RECEIPT --------------------

@router.message(F.photo | F.document)
async def receipt_handler(message: Message):
    # Ищем только SOS объявления пользователя, которые ожидают оплаты
    user_ads = [
        (ad_id, ad)
        for ad_id, ad in PENDING_ADS.items()
        if ad["user_id"] == message.from_user.id and ad.get("type") == "sos"
    ]

    if not user_ads:
        return

    ad_id, _ = user_ads[0]

    user = message.from_user

    username = f"@{user.username}" if user.username else "—"

    caption = (
        "💳 Чек оплаты\n\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}"
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

    await message.answer(
        "📎 Чек получен.\n"
        "⏳ Ожидайте подтверждения модератора.",
        reply_markup=main_reply_menu()
    )


# -------------------- ADMIN: PUBLISH --------------------

@router.callback_query(F.data.startswith("admin:publish:"))
async def admin_publish(callback: CallbackQuery):
    ad_id = int(callback.data.split(":")[2])
    ad = PENDING_ADS.get(ad_id)

    if not ad:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    ad_type = ad.get("type", "regular")
    
    if ad_type == "sos":
        # SOS объявления публикуются без фото (только текст)
        await callback.bot.send_message(
            CHANNEL_ID,
            text=ad["public_caption"]
        )
    else:
        # Обычные объявления публикуются с фото
        await callback.bot.send_photo(
            CHANNEL_ID,
            photo=ad["photo"],
            caption=ad["public_caption"]
        )

    await callback.bot.send_message(
        ad["user_id"],
        "🎉 Ваше объявление опубликовано в канале UNI Swap!\n"
        "Спасибо за использование платформы ♻️",
        reply_markup=main_reply_menu()
    )

    del PENDING_ADS[ad_id]

    await callback.message.answer("✅ Объявление опубликовано")
    await callback.answer()


# -------------------- ADMIN: REJECT --------------------

@router.callback_query(F.data.startswith("admin:reject:"))
async def admin_reject(callback: CallbackQuery):
    ad_id = int(callback.data.split(":")[2])
    ad = PENDING_ADS.get(ad_id)

    if not ad:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    message_text = callback.message.text or ""
    message_caption = callback.message.caption or ""

    is_receipt = "Чек оплаты" in message_caption or "Чек оплаты" in message_text

    if is_receipt:
        # ❌ ОТКЛОНЁН ЧЕК — заявка остаётся
        await callback.bot.send_message(
            ad["user_id"],
            "❌ Чек отклонён модератором.\n\n"
            "Пожалуйста, отправьте корректный чек об оплате ещё раз.",
            reply_markup=main_reply_menu()
        )

        await callback.message.answer(
            "❌ Чек отклонён. Ожидаем новый чек от пользователя."
        )

    else:
        # ❌ ОТКЛОНЕНО ОБЪЯВЛЕНИЕ — заявка удаляется
        await callback.bot.send_message(
            ad["user_id"],
            "❌ Ваше объявление отклонено модератором.\n\n"
            "Вы можете подать объявление заново.",
            reply_markup=main_reply_menu()
        )

        del PENDING_ADS[ad_id]

        await callback.message.answer("❌ Объявление отклонено.")

    await callback.answer("Отклонено")


@router.callback_query(F.data == "retry_receipt")
async def retry_receipt(callback: CallbackQuery):
    await callback.message.answer(
        "📎 Пожалуйста, отправьте чек об оплате (PDF или фото).",
        reply_markup=main_reply_menu()
    )
    await callback.answer()


@router.message(F.text == "📞 Связь с админом")
async def admin_contact_handler(message: Message, state: FSMContext):
    """Обработчик текстовой кнопки 'Связь с админом'"""
    await state.clear()  # Очищаем состояние FSM, если было активно
    await message.answer(
        "📞 Связь с администратором:\n\n"
        "👤 @Adlet_KK\n\n"
        "Напишите администратору для решения вопросов.",
        reply_markup=main_reply_menu()
    )

