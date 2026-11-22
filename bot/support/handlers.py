import logging

import httpx
from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.services.orders import get_user_orders
from bot.states import SupportStates
from bot.support.faq import ALL_QUESTIONS, FAQ, find_questions
from bot.support.keyboards import (
    PROBLEMS,
    category_keyboard,
    menu_keyboard,
    problem_steps_keyboard,
    problems_keyboard,
    question_keyboard,
    search_results_keyboard,
)

router = Router()
HOME_TEXT = (
    "🌙 Центр помощи Luna Market\n\n"
    "Привет! Я помогу разобраться с заказами, активацией игр, аккаунтом и другими вопросами.\n\n"
    "Выбери интересующий раздел:"
)
QUESTION_BY_ID = {question["id"]: question for question in ALL_QUESTIONS}


async def show(callback: CallbackQuery, text: str, keyboard=None):
    """Редактирует экран центра; если это невозможно, отправляет новый."""
    message = callback.message
    if not isinstance(message, Message):
        await callback.answer("Экран недоступен", show_alert=True)
        return
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramAPIError as exc:
        if "message is not modified" in str(exc).casefold():
            return
        try:
            await message.answer(text, reply_markup=keyboard)
        except TelegramAPIError:
            logging.exception("Не удалось показать экран Центра помощи")


@router.message(F.text == "💬 Поддержка")
async def support_entry(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HOME_TEXT, reply_markup=menu_keyboard())


@router.callback_query(F.data == "sup:home")
async def support_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await show(callback, HOME_TEXT, menu_keyboard())


@router.callback_query(F.data.startswith("sup:cat:"))
async def support_category(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    category_id = callback.data.removeprefix("sup:cat:")
    category = FAQ.get(category_id)
    await callback.answer()
    if not category:
        await show(callback, "Этот раздел уже недоступен.", menu_keyboard())
        return
    await show(callback, f"{category['title']}\n\nВыберите вопрос:", category_keyboard(category_id))


@router.callback_query(F.data.startswith("sup:q:"))
async def support_question(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    question_id = callback.data.removeprefix("sup:q:")
    question = QUESTION_BY_ID.get(question_id)
    await callback.answer()
    if not question:
        await show(callback, "Вопрос больше недоступен. Выберите раздел:", menu_keyboard())
        return
    await show(callback, f"{question['title']}\n\n{question['answer']}", question_keyboard(question["category"]))


@router.callback_query(F.data == "sup:search")
async def begin_faq_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.waiting_for_faq_query)
    await callback.answer()
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить поиск", callback_data="sup:cancel_search")],
        [InlineKeyboardButton(text="🏠 Главное меню поддержки", callback_data="sup:home")],
    ])
    await show(callback, "🔎 Найти ответ\n\nНапишите вопрос одним сообщением. Максимум 200 символов.", keyboard)


@router.callback_query(F.data == "sup:cancel_search")
async def cancel_faq_search(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Поиск отменён")
    await show(callback, HOME_TEXT, menu_keyboard())


@router.message(SupportStates.waiting_for_faq_query, F.text)
async def faq_search_query(message: Message, state: FSMContext):
    if message.text.strip().casefold() == "/cancel":
        await state.clear()
        await message.answer("Поиск FAQ отменён. Откройте «💬 Поддержка», чтобы продолжить.")
        return
    query = message.text.strip()
    if not query:
        await message.answer("Введите текст вопроса или отмените поиск кнопкой ниже.")
        return
    if len(query) > 200:
        await message.answer("Вопрос слишком длинный. Максимум 200 символов. Сократите его или отмените поиск.")
        return
    results = find_questions(query)
    await state.clear()
    if not results:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔎 Искать ещё", callback_data="sup:search")],
            [InlineKeyboardButton(text="🏠 Главное меню поддержки", callback_data="sup:home")],
        ])
        await message.answer("😕 Не нашёл подходящего ответа. Попробуйте другие слова или выберите раздел помощи.", reply_markup=keyboard)
        return
    await message.answer("🔎 Нашёл подходящие вопросы. Выберите нужный:", reply_markup=search_results_keyboard(results))


@router.message(SupportStates.waiting_for_faq_query)
async def faq_search_invalid(message: Message):
    await message.answer("Отправьте вопрос текстом или отмените поиск кнопкой в Центре помощи.")


@router.callback_query(F.data == "sup:problems")
async def support_problems(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await show(callback, "🛠 Помощь с проблемой\n\nВыберите, что случилось:", problems_keyboard())


@router.callback_query(F.data.startswith("sup:problem:"))
async def support_problem(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    problem_id = callback.data.removeprefix("sup:problem:")
    scenario = PROBLEMS.get(problem_id)
    await callback.answer()
    if not scenario:
        await show(callback, "Этот сценарий недоступен.", problems_keyboard())
        return
    title, steps = scenario
    step, body = steps[0]
    text = f"🛠 {title}\n\nШаг 1 из {len(steps)} · {step}\n{body}"
    if problem_id == "missing":
        text += "\n\nПроверку списка можно запустить кнопкой ниже."
    await show(callback, text, problem_steps_keyboard(problem_id, 0, len(steps)))


@router.callback_query(F.data.startswith("sup:step:"))
async def support_problem_step(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        _, _, problem_id, raw_step = callback.data.split(":")
        step_index = int(raw_step)
    except (ValueError, AttributeError):
        await callback.answer("Некорректный шаг", show_alert=True)
        return
    scenario = PROBLEMS.get(problem_id)
    if not scenario or not 0 <= step_index < len(scenario[1]):
        await callback.answer("Этот шаг недоступен", show_alert=True)
        return
    title, steps = scenario
    await callback.answer()
    if problem_id == "missing" and step_index == 1:
        await show(callback, "⏳ Проверяю заказы для вашего Telegram…")
        if not isinstance(callback.message, Message) or callback.message.chat.type != "private":
            await show(callback, "🔒 Проверка заказов доступна только в личном чате с ботом.", problem_steps_keyboard(problem_id, step_index, len(steps)))
            return
        try:
            orders = await get_user_orders(callback.from_user.id)
            if orders is None:
                body = "Telegram не привязан к аккаунту Luna Market. Подключите его в профиле сайта и повторите проверку."
            elif not orders:
                body = "Для аккаунта, привязанного к этому Telegram, заказов не найдено. Проверьте, что заказ оформлялся в этом аккаунте."
            else:
                counts = {"PENDING": 0, "PAID": 0, "CANCELLED": 0}
                for order in orders:
                    status = order.get("status") if isinstance(order, dict) else None
                    if status in counts:
                        counts[status] += 1
                body = (f"Найдено заказов: {len(orders)}. "
                        f"Ожидают оплаты: {counts['PENDING']}; оплачены: {counts['PAID']}; отменены: {counts['CANCELLED']}.\n\n"
                        "Для подробного просмотра откройте «📦 Мои заказы» или /orders. Здесь отображаются только количества и статусы, без ключей и данных других пользователей.")
        except (httpx.HTTPError, ValueError, TypeError, RuntimeError):
            logging.exception("Не удалось проверить заказы в Центре помощи")
            body = "Сейчас не удалось связаться с сервисом заказов. Попробуйте позже или откройте «📦 Мои заказы»."
    else:
        _, body = steps[step_index]
    text = f"🛠 {title}\n\nШаг {step_index + 1} из {len(steps)} · {steps[step_index][0]}\n{body}"
    await show(callback, text, problem_steps_keyboard(problem_id, step_index, len(steps)))


@router.callback_query(F.data.startswith("sup:"))
async def support_stale_callback(callback: CallbackQuery):
    await callback.answer("Кнопка устарела. Откройте Центр помощи заново.", show_alert=True)
