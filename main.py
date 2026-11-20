from bot.telegram_link import router as telegram_link_router
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot.handlers import router

# Загружаем .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# Включаем логирование
logging.basicConfig(level=logging.INFO)


async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не найден в .env")

    # Создаём бота и диспетчер
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем обработчики
    dp.include_router(telegram_link_router)
    dp.include_router(router)

    logging.info("🌙 Luna Market Bot запущен!")

    try:
        # Начинаем получать сообщения
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
