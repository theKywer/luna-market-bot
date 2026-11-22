
import logging

import httpx

from aiogram import F, Router
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import (
    main_menu,
    catalog_keyboard,
    search_results_keyboard,
)
from bot.states import SearchStates
from bot.services.games import get_games


router = Router()


# Подготовка каталога
def prepare_games(games):
    valid_games = [
        game
        for game in games
        if isinstance(game, dict)
        and type(game.get("id")) is int
        and game["id"] > 0
    ]

    return sorted(
        valid_games,
        key=lambda game: game["id"],
    )


# Сокращаем длинный текст
def shorten(value, limit):
    text = str(value or "—").strip()

    if len(text) > limit:
        return text[:limit - 1] + "…"

    return text


# Формирование карточки
def format_game(game, index, total):
    title = shorten(game.get("title"), 100)
    genre = shorten(game.get("genre"), 60)
    platform = shorten(game.get("platform"), 60)
    description = shorten(game.get("description"), 350)

    price = game.get("price")
    old_price = game.get("oldPrice")
    discount = game.get("discount")

    if type(price) is int:
        price_text = f"{price:,}".replace(",", " ") + " ₸"
    else:
        price_text = "не указана"

    lines = [
        f"🎮 {title}",
        "",
        f"🎭 Жанр: {genre}",
        f"🖥 Платформа: {platform}",
        f"💰 Цена: {price_text}",
    ]

    if (
        type(price) is int
        and type(old_price) is int
        and old_price > price
    ):
        old_text = f"{old_price:,}".replace(",", " ")
        lines.append(f"🏷 Старая цена: {old_text} ₸")

    if type(discount) is int and discount > 0:
        lines.append(f"🔥 Скидка: {discount}%")

    lines.extend([
        "",
        f"📝 {description}",
        "",
        f"📄 Игра {index + 1} из {total}",
    ])

    return "\n".join(lines)


# Отправка карточки
async def send_game_card(message, games, index):
    game = games[index]

    text = format_game(game, index, len(games))

    keyboard = catalog_keyboard(
        index,
        len(games),
        game["id"],
    )

    image = game.get("image")

    if isinstance(image, str) and image.startswith("https://"):
        try:
            return await message.answer_photo(
                photo=image,
                caption=text,
                reply_markup=keyboard,
            )

        except TelegramBadRequest:
            logging.warning(
                "Не удалось загрузить изображение игры %s",
                game["id"],
            )

    return await message.answer(
        text,
        reply_markup=keyboard,
    )


# Команда /start
@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "🌙 Добро пожаловать в Luna Market!\n\n"
        "Выберите интересующий вас раздел:",
        reply_markup=main_menu,
    )


# Команда /help
@router.message(Command("help"))
async def help_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "📋 Доступные команды:\n\n"
        "/start — Главное меню\n"
        "/help — Помощь\n"
        "/cancel — Отменить поиск",
        reply_markup=main_menu,
    )


# Отмена поиска
@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "❌ Поиск отменён.",
        reply_markup=main_menu,
    )


# Открытие каталога
@router.message(F.text == "🎮 Каталог игр")
async def catalog_handler(message: Message, state: FSMContext):
    await state.clear()

    try:
        games = prepare_games(await get_games())

        if not games:
            await message.answer(
                "🎮 В каталоге пока нет игр."
            )
            return

        await send_game_card(message, games, 0)

    except (httpx.HTTPError, ValueError, TypeError):
        logging.exception("Ошибка загрузки каталога")

        await message.answer(
            "❌ Не удалось загрузить каталог игр."
        )


# Переключение страниц каталога
@router.callback_query(F.data.regexp(r"^catalog:\d+$"))
async def catalog_page_handler(callback: CallbackQuery):
    await callback.answer()

    if not isinstance(callback.message, Message):
        return

    try:
        index = int(callback.data.split(":")[1])

        games = prepare_games(await get_games())

        if index >= len(games):
            await callback.message.answer(
                "Эта игра больше недоступна."
            )
            return

        await send_game_card(
            callback.message,
            games,
            index,
        )

        try:
            await callback.message.delete()

        except (TelegramBadRequest, TelegramForbiddenError):
            logging.warning(
                "Не удалось удалить предыдущую карточку"
            )

    except (httpx.HTTPError, ValueError, TypeError):
        logging.exception("Ошибка переключения каталога")

        await callback.message.answer(
            "❌ Не удалось открыть игру."
        )


# Начало поиска
@router.message(F.text == "🔎 Поиск")
async def search_handler(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_query)

    await message.answer(
        "🔎 Поиск игр\n\n"
        "Введите название игры, которую хотите найти.\n\n"
        "Например: Cyberpunk, Witcher, Elden Ring.\n\n"
        "Для отмены используйте /cancel."
    )


# Обработка введённого названия
@router.message(SearchStates.waiting_for_query, F.text)
async def search_query_handler(
    message: Message,
    state: FSMContext,
):
    query = message.text.strip()

    if len(query) < 2:
        await message.answer(
            "⚠️ Введите хотя бы 2 символа."
        )
        return

    if len(query) > 80:
        await message.answer(
            "⚠️ Название слишком длинное.\n"
            "Максимум 80 символов."
        )
        return

    try:
        games = prepare_games(await get_games())

        # Поиск без учёта регистра
        matches = [
            game
            for game in games
            if query.casefold()
            in str(game.get("title") or "").casefold()
        ]

        if not matches:
            await message.answer(
                "😕 Ничего не найдено.\n\n"
                "Попробуйте другое название или /cancel."
            )
            return

        # Ограничиваем выдачу
        results = matches[:10]

        lines = [
            "🔎 Результаты поиска",
            "",
            f"По запросу «{query}» найдено: {len(matches)}",
            "",
        ]

        for index, game in enumerate(results, start=1):
            title = shorten(game.get("title"), 80)
            price = game.get("price")

            if type(price) is int:
                price_text = f"{price:,}".replace(",", " ") + " ₸"
            else:
                price_text = "цена не указана"

            lines.append(
                f"{index}. {title} — {price_text}"
            )

        if len(matches) > 10:
            lines.append(
                "\nПоказаны первые 10 результатов."
            )

        lines.append(
            "\nВыберите игру с помощью кнопок ниже."
        )

        await state.clear()

        await message.answer(
            "\n".join(lines),
            reply_markup=search_results_keyboard(results),
        )

    except (httpx.HTTPError, ValueError, TypeError):
        logging.exception("Ошибка поиска игр")

        await message.answer(
            "❌ Не удалось выполнить поиск.\n"
            "Попробуйте ещё раз."
        )


# Открытие игры из результатов поиска
@router.callback_query(F.data.regexp(r"^search_game:\d+$"))
async def search_game_handler(callback: CallbackQuery):
    await callback.answer()

    if not isinstance(callback.message, Message):
        return

    try:
        game_id = int(callback.data.split(":")[1])

        games = prepare_games(await get_games())

        for index, game in enumerate(games):
            if game["id"] == game_id:
                await send_game_card(
                    callback.message,
                    games,
                    index,
                )
                return

        await callback.message.answer(
            "😕 Эта игра больше недоступна."
        )

    except (httpx.HTTPError, ValueError, TypeError):
        logging.exception("Ошибка открытия игры")

        await callback.message.answer(
            "❌ Не удалось открыть игру."
        )


# Нетекстовое сообщение во время поиска
@router.message(SearchStates.waiting_for_query)
async def search_invalid_handler(message: Message):
    await message.answer(
        "🔎 Отправьте название игры текстом.\n"
        "Для отмены используйте /cancel."
    )


# Мои заказы


# Поддержка
@router.message(F.text == "💬 Поддержка")
async def support_handler(message: Message, state: FSMContext):
    await state.clear()

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
