
import logging
from datetime import datetime, timezone

import httpx

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.services.orders import get_user_orders

router = Router()


# Форматируем цену
def money(value):
    if type(value) is int:
        return f"{value:,}".replace(",", " ") + " ₸"

    return "—"


# Форматируем дату заказа
def date_label(value):
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        return parsed.astimezone(timezone.utc).strftime(
            "%d.%m.%Y, %H:%M UTC"
        )

    except (AttributeError, ValueError, TypeError):
        return "Дата неизвестна"


# Формируем текст карточки заказа
def order_text(order, index, total):
    status_labels = {
        "PENDING": "⏳ Ожидает оплаты",
        "PAID": "✅ Оплачен",
        "CANCELLED": "❌ Отменён",
    }

    status = status_labels.get(
        order.get("status"),
        "Неизвестен",
    )

    lines = [
        f"📦 Заказ #{order['id']}",
        f"📅 {date_label(order.get('createdAt'))}",
        f"📌 Статус: {status}",
        "",
        "🎮 Игры:",
    ]

    items = order.get("items") or []

    for item in items[:15]:
        title = str(
            item.get("gameTitle") or "Игра"
        )[:80]

        quantity = item.get("quantity", 1)
        unit_price = item.get("unitPrice")

        if (
            type(unit_price) is int
            and type(quantity) is int
        ):
            line_total = money(unit_price * quantity)
        else:
            line_total = "—"

        lines.append(
            f"• {title} × {quantity} — {line_total}"
        )

    if len(items) > 15:
        lines.append(
            f"…и ещё {len(items) - 15} позиций"
        )

    lines.extend([
        "",
        f"💰 Сумма заказа: {money(order.get('totalAmount'))}",
        f"📄 {index + 1} из {total} последних заказов",
    ])

    return "\n".join(lines)


# Кнопки переключения заказов
def order_keyboard(orders, index):
    buttons = []

    if index > 0:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Новее",
                callback_data=(
                    f"orders:show:{orders[index - 1]['id']}"
                ),
            )
        )

    if index < len(orders) - 1:
        buttons.append(
            InlineKeyboardButton(
                text="Старее ➡️",
                callback_data=(
                    f"orders:show:{orders[index + 1]['id']}"
                ),
            )
        )

    rows = [buttons] if buttons else []

    rows.append([
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data=(
                f"orders:show:{orders[index]['id']}"
            ),
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=rows,
    )


# Открытие истории заказов
@router.message(Command("orders"))
@router.message(F.text == "📦 Мои заказы")
async def orders_handler(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    if message.chat.type != ChatType.PRIVATE:
        await message.answer(
            "🔒 Заказы доступны только в личном чате."
        )
        return

    if not message.from_user:
        return

    try:
        orders = await get_user_orders(
            message.from_user.id
        )

        if orders is None:
            await message.answer(
                "🔗 Telegram ещё не привязан "
                "к аккаунту Luna Market.\n\n"
                "Откройте профиль на сайте "
                "и подключите Telegram."
            )
            return

        if not orders:
            await message.answer(
                "📦 У вас пока нет заказов."
            )
            return

        await message.answer(
            order_text(orders[0], 0, len(orders)),
            reply_markup=order_keyboard(orders, 0),
        )

    except (
        httpx.HTTPError,
        ValueError,
        TypeError,
        RuntimeError,
    ):
        logging.exception("Ошибка получения заказов")

        await message.answer(
            "❌ Не удалось загрузить заказы.\n"
            "Попробуйте позже."
        )


# Переключение заказов
@router.callback_query(
    F.data.regexp(r"^orders:show:\d+$")
)
async def show_order_handler(callback: CallbackQuery):
    if not isinstance(callback.message, Message):
        await callback.answer(
            "Карточка недоступна",
            show_alert=True,
        )
        return

    if callback.message.chat.type != ChatType.PRIVATE:
        await callback.answer(
            "Откройте личный чат с ботом",
            show_alert=True,
        )
        return

    await callback.answer()

    try:
        orders = await get_user_orders(
            callback.from_user.id
        )

        if orders is None:
            await callback.message.edit_text(
                "🔗 Telegram больше не привязан.\n"
                "Подключите его в профиле сайта."
            )
            return

        target_id = int(
            callback.data.rsplit(":", 1)[1]
        )

        index = next(
            (
                i for i, order in enumerate(orders)
                if order["id"] == target_id
            ),
            None,
        )

        if index is None:
            await callback.message.edit_text(
                "📦 Заказ недоступен в последних "
                "20 записях.\n"
                "Откройте «Мои заказы» заново."
            )
            return

        try:
            await callback.message.edit_text(
                order_text(
                    orders[index],
                    index,
                    len(orders),
                ),
                reply_markup=order_keyboard(
                    orders,
                    index,
                ),
            )

        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                raise

    except (
        httpx.HTTPError,
        ValueError,
        TypeError,
        RuntimeError,
        TelegramBadRequest,
    ):
        logging.exception("Ошибка просмотра заказа")

        await callback.message.answer(
            "❌ Не удалось обновить заказ.\n"
            "Попробуйте ещё раз."
        )
