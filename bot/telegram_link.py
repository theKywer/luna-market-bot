
import logging
import os
import re

import httpx

from aiogram import Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

router = Router()

API_URL = os.getenv(
    "LUNA_API_URL",
    "http://localhost:3001",
).rstrip("/")

BRIDGE_SECRET = os.getenv("TELEGRAM_BRIDGE_SECRET")


@router.message(CommandStart(deep_link=True))
async def link_telegram(message: Message, command: CommandObject):
    if message.chat.type != ChatType.PRIVATE:
        await message.answer(
            "🔒 Привязать аккаунт можно только в личном чате."
        )
        return

    argument = command.args or ""

    if not argument.startswith("link_"):
        await message.answer("🌙 Добро пожаловать в Luna Market!")
        return

    token = argument.removeprefix("link_")

    if not re.fullmatch(r"[a-f0-9]{48}", token):
        await message.answer("❌ Некорректная ссылка привязки.")
        return

    if not BRIDGE_SECRET:
        logging.error("TELEGRAM_BRIDGE_SECRET не настроен")
        await message.answer("❌ Сервис привязки пока недоступен.")
        return

    if not message.from_user:
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{API_URL}/telegram/consume",
                headers={
                    "X-Telegram-Bot-Secret": BRIDGE_SECRET,
                },
                json={
                    "token": token,
                    "telegramUserId": str(message.from_user.id),
                },
            )

            logging.info(
                "Telegram consume: HTTP %s | %s",
                    response.status_code,
                    response.json().get("message", "Нет сообщения"),
            )

        if response.status_code == 200:
            await message.answer(
                "✅ Telegram успешно привязан к Luna Market!\n\n"
                "Теперь вы сможете пользоваться функциями "
                "своего аккаунта прямо в боте."
            )

        elif response.status_code == 410:
            await message.answer(
                "⌛ Ссылка устарела или уже использована.\n"
                "Создайте новую в профиле Luna Market."
            )

        elif response.status_code == 409:
            await message.answer(
                "⚠️ Аккаунт или Telegram уже привязан.\n"
                "Проверьте подключение в профиле сайта."
            )

        else:
            logging.error(
                "Ошибка привязки, HTTP %s",
                response.status_code,
            )
            await message.answer(
                "❌ Не удалось привязать аккаунт."
            )

    except httpx.RequestError:
        logging.exception("Ошибка соединения с Luna Market API")
        await message.answer(
            "❌ Сервер Luna Market недоступен."
        )
