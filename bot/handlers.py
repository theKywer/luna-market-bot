
import logging

import httpx

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.keyboards import main_menu
from bot.services.games import get_games

router = Router()


# Главное меню
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🌙 Добро пожаловать в Luna Market!\n\n"
        "Выберите интересующий вас раздел:",
        reply_markup=main_menu,
    )


# Помощь
@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📋 Доступные команды:\n\n"
        "/start — Главное меню\n"
        "/help — Помощь",
        reply_markup=main_menu,
    )


# Каталог игр
@router.message(F.text == "🎮 Каталог игр")
async def catalog_handler(message: Message):
    try:
        games = await get_games()

        if not games:
            await message.answer(
                "🎮 В каталоге пока нет игр."
            )
            return

        lines = ["🎮 Каталог Luna Market"]

        # Показываем первые 10 игр
        for index, game in enumerate(games[:10], start=1):
            title = str(
                game.get("title") or "Без названия"
            )[:100]

            price = game.get("price")

            if isinstance(price, (int, float)):
                price_text = f"{price:,}".replace(",", " ")
            else:
                price_text = "не указана"

            lines.append(
                f"{index}. {title}\n"
                f"Цена: {price_text}"
            )

        if len(games) > 10:
            lines.append(
                f"Показаны первые 10 из {len(games)} игр."
            )

        await message.answer("\n\n".join(lines))

    except (httpx.HTTPError, ValueError, TypeError):
        logging.exception("Ошибка загрузки каталога")

        await message.answer(
            "❌ Не удалось загрузить каталог игр.\n"
            "Попробуйте позже."
        )


# Поиск
@router.message(F.text == "🔎 Поиск")
async def search_handler(message: Message):
    await message.answer(
        "🔎 Поиск игр\n\n"
        "Скоро здесь появится поиск по каталогу."
    )


# Мои заказы
@router.message(F.text == "📦 Мои заказы")
async def orders_handler(message: Message):
    await message.answer(
        "📦 Мои заказы\n\n"
        "Скоро здесь появится история заказов."
    )


# Поддержка
@router.message(F.text == "💬 Поддержка")
async def support_handler(message: Message):
    await message.answer(
        "💬 Поддержка Luna Market\n\n"
        "Раздел находится в разработке."
    )


# Неизвестные сообщения
@router.message()
async def unknown_handler(message: Message):
    await message.answer(
        "Неизвестная команда.\n"
        "Выберите раздел в меню.",
        reply_markup=main_menu,
    )
