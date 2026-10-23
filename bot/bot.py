"""
Телеграм-бот хозяйства «Дежкино» (aiogram 3)
Поддерживает как Telegram Mini App, так и текстовый каталог с кнопками в чате.
"""

import asyncio
import json
import logging
import os
import sys

# Обеспечиваем корректный вывод UTF-8 в консоли Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, MenuButtonWebApp
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.json")


def get_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌾 Открыть витрину Дежкино (Mini App)",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ],
            [
                InlineKeyboardButton(text="🍗 Мясо и птица", callback_data="cat_meat"),
                InlineKeyboardButton(text="🥚 Яйца", callback_data="cat_eggs")
            ],
            [
                InlineKeyboardButton(text="🍯 Мёд и пасека", callback_data="cat_honey"),
                InlineKeyboardButton(text="🌿 Сезонное", callback_data="cat_seasonal")
            ],
            [
                InlineKeyboardButton(text="📞 Связаться с фермером", callback_data="action_contact")
            ]
        ]
    )


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Приветственное сообщение"""
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}!\n\n"
        "Добро пожаловать в семейное хозяйство **«Дежкино»**.\n"
        "Мы выращиваем натуральную птицу, держим пасеку и собираем сезонный урожай без химии и антибиотиков.\n\n"
        "Выберите удобный способ заказа:\n"
        "• Откройте интерактивную **витрину (Mini App)**\n"
        "• Или выберите категорию кнопками ниже 👇",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("cat_"))
async def handle_category(callback: types.CallbackQuery):
    cat_id = callback.data.replace("cat_", "")
    cat_names = {
        "meat": "🍗 Мясо и птица",
        "eggs": "🥚 Яйца",
        "honey": "🍯 Мёд и пасека",
        "seasonal": "🌿 Сезонное и травы"
    }

    products = [p for p in get_products() if p.get("category") == cat_id]

    if not products:
        text = f"В категории *{cat_names.get(cat_id, 'Товары')}* пока нет позиций."
    else:
        text = f"*{cat_names.get(cat_id, 'Ассортимент')}:*\n\n"
        for p in products:
            status = "✅ В наличии" if p.get("inStock", True) else "❌ Раскуплено"
            text += f"{p['icon']} *{p['name']}*\n"
            text += f"💰 {p['price']} ₽ ({p['unit']}) — {status}\n"
            text += f"_{p['desc']}_\n\n"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌾 Заказать через Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="← Назад в меню", callback_data="menu_back")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "action_contact")
async def handle_contact(callback: types.CallbackQuery):
    text = (
        "📍 **Семейное хозяйство «Дежкино»**\n\n"
        "• **Локация:** деревня Дежкино\n"
        "• **Доставка:** доставляем свежие заказы в город по договоренности\n"
        "• **Телефон / WhatsApp:** +7 (999) 000-00-00\n"
        "• **По всем вопросам:** пишите нам прямо в этот чат!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌾 Открыть витрину", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton(text="← Назад в меню", callback_data="menu_back")]
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data == "menu_back")
async def handle_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите раздел или откройте витрину:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    """Прием данных заказа из Telegram Mini App"""
    try:
        data = json.loads(message.web_app_data.data)
        client = data.get("client", {})
        items = data.get("items", [])
        total = data.get("total", 0)

        items_text = "\n".join([f"• {i['name']} ({i['qty']} шт.) = {i['subtotal']} ₽" for i in items])

        summary = (
            "🔔 **НОВЫЙ ЗАКАЗ ИЗ ДЕЖКИНО!**\n\n"
            f"👤 **Покупатель:** {client.get('name')}\n"
            f"📞 **Телефон:** {client.get('phone')}\n"
            f"📍 **Адрес / доставка:** {client.get('address')}\n"
            f"💬 **Telegram:** @{message.from_user.username or 'не указан'} (ID: {message.from_user.id})\n\n"
            f"🛒 **Состав заказа:**\n{items_text}\n\n"
            f"💰 **Итого к оплате:** {total} ₽"
        )

        await message.answer(
            f"✅ **Спасибо за заказ, {client.get('name')}!**\n\n"
            f"Ваша заявка на сумму **{total} ₽** принята.\n"
            "Мы свяжемся с вами в ближайшее время для уточнения времени доставки.",
            parse_mode="Markdown"
        )

        if ADMIN_CHAT_ID:
            await bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=summary,
                parse_mode="Markdown"
            )

    except Exception as e:
        logging.error(f"Ошибка при обработке заказа: {e}")
        await message.answer("Произошла ошибка при обработке данных заказа. Пожалуйста, свяжитесь с нами напрямую.")


async def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN":
        print("[!] Внимание: Укажите реальный BOT_TOKEN в файле bot/.env")

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🌾 Витрина Дежкино", web_app=WebAppInfo(url=WEBAPP_URL))
        )
        print(f"[OK] Telegram MenuButton установлен на URL: {WEBAPP_URL}")
    except Exception as e:
        print(f"[!] Не удалось установить MenuButton: {e}")

    print("[OK] Бот Дежкино запущен и ожидает событий...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
