
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv(
    "LUNA_API_URL",
    "http://localhost:3001",
).rstrip("/")


async def get_games():
    # Отправляем GET-запрос на сервер Luna Market
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{API_URL}/games")

        # Проверяем, что сервер ответил без ошибки
        response.raise_for_status()

        # Преобразуем JSON в объекты Python
        games = response.json()

        if not isinstance(games, list):
            raise ValueError("API вернул некорректный каталог")

        return games
