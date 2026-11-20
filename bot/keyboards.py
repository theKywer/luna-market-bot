
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню Luna Market
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎮 Каталог игр"),
            KeyboardButton(text="🔎 Поиск"),
        ],
        [
            KeyboardButton(text="📦 Мои заказы"),
            KeyboardButton(text="💬 Поддержка"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите раздел...",
)
