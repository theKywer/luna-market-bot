
import logging

logging.basicConfig(level=logging.INFO)

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# Создаём диспетчер для обработки сообщений
dp = Dispatcher()


# Обрабатываем команду /start
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "🌙 Добро пожаловать в Luna Market!\n\n"
        "Я бот игрового магазина.\n"
        "Скоро здесь появятся каталог игр, "
        "поиск и информация о заказах.\n\n"
        "Используй /help для просмотра команд."
    )


# Обрабатываем команду /help
@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📋 Доступные команды:\n\n"
        "/start — Главное меню\n"
        "/help — Список команд"
    )


# Точка входа в программу
async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не найден в .env")

    bot = Bot(token=TOKEN)

    print("🌙 Luna Market Bot запускается...")

    # Начинаем получать сообщения из Telegram
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
