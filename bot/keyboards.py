
import os
from urllib.parse import urlparse

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# Главное меню
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


# Кнопки каталога
def catalog_keyboard(index, total, game_id):
    rows = []
    navigation = []

    if index > 0:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"catalog:{index - 1}",
            )
        )

    if index < total - 1:
        navigation.append(
            InlineKeyboardButton(
                text="Вперёд ➡️",
                callback_data=f"catalog:{index + 1}",
            )
        )

    if navigation:
        rows.append(navigation)

    # Переход на публичный сайт
    site_url = os.getenv("LUNA_SITE_URL", "").strip().rstrip("/")
    parsed = urlparse(site_url)

    if (
        parsed.scheme == "https"
        and parsed.hostname
        and parsed.hostname not in ("localhost", "127.0.0.1")
    ):
        rows.append([
            InlineKeyboardButton(
                text="🌐 Открыть на сайте",
                url=f"{site_url}/game/{game_id}",
            )
        ])

    if not rows:
        return None

    return InlineKeyboardMarkup(inline_keyboard=rows)


# Кнопки результатов поиска
def search_results_keyboard(games):
    rows = []

    for game in games:
        title = str(game.get("title") or "Без названия")

        rows.append([
            InlineKeyboardButton(
                text=f"🎮 {title[:45]}",
                callback_data=f"search_game:{game['id']}",
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
