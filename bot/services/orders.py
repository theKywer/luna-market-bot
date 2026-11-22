
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv(
    "LUNA_API_URL",
    "http://localhost:3001",
).rstrip("/")

BRIDGE_SECRET = os.getenv("TELEGRAM_BRIDGE_SECRET")


async def get_user_orders(telegram_user_id: int):
    if not BRIDGE_SECRET:
        raise RuntimeError(
            "TELEGRAM_BRIDGE_SECRET не настроен"
        )

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{API_URL}/telegram/orders",
            headers={
                "X-Telegram-Bot-Secret": BRIDGE_SECRET,
            },
            json={
                "telegramUserId": str(telegram_user_id),
            },
        )

    # Пользователь не привязан к сайту
    if response.status_code == 404:
        data = response.json()

        if data.get("code") == "TELEGRAM_NOT_LINKED":
            return None

    # Любые другие ошибки API
    response.raise_for_status()

    data = response.json()
    orders = data.get("orders")

    if not isinstance(orders, list):
        raise ValueError("Некорректный ответ API заказов")

    return orders
