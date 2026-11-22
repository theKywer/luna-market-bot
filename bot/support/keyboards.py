from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.support.faq import FAQ


def menu_keyboard():
    rows = [
        [InlineKeyboardButton(text=category["title"], callback_data=f"sup:cat:{key}")]
        for key, category in FAQ.items()
    ]
    rows.extend([
        [InlineKeyboardButton(text="🔎 Найти ответ", callback_data="sup:search")],
        [InlineKeyboardButton(text="🛠 Помощь с проблемой", callback_data="sup:problems")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_keyboard(category_id):
    category = FAQ.get(category_id)
    if not category:
        return None
    rows = [[InlineKeyboardButton(text=q["title"], callback_data=f"sup:q:{q['id']}")] for q in category["questions"]]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="sup:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def question_keyboard(category_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"sup:cat:{category_id}")],
        [InlineKeyboardButton(text="🏠 Главное меню поддержки", callback_data="sup:home")],
    ])


def search_results_keyboard(results):
    rows = [[InlineKeyboardButton(text=f"{q['category_title']} · {q['title']}"[:60], callback_data=f"sup:q:{q['id']}")] for q in results]
    rows.extend([
        [InlineKeyboardButton(text="🔎 Искать ещё", callback_data="sup:search")],
        [InlineKeyboardButton(text="🏠 Главное меню поддержки", callback_data="sup:home")],
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


PROBLEMS = {
    "missing": ("Не вижу свой заказ", [
        ("Проверить привязку", "Откройте профиль на сайте Luna Market и убедитесь, что привязан именно этот Telegram. Заказы доступны только из привязанного аккаунта."),
        ("Проверить список", "Сейчас проверю список заказов, доступный этому Telegram."),
    ]),
    "status": ("Не понимаю статус заказа", [
        ("PENDING", "Заказ ожидает оплаты. Бот показывает статус, полученный от сервиса Luna Market."),
        ("PAID", "Заказ отмечен как оплаченный сервисом Luna Market."),
        ("CANCELLED", "Заказ отменён. Бот не располагает дополнительными сведениями о причине отмены."),
    ]),
    "login": ("Не могу войти в аккаунт", [
        ("Проверить вход", "Проверьте данные входа на сайте Luna Market и используйте доступные на сайте средства восстановления."),
        ("Безопасность", "Не отправляйте боту пароль, JWT или другие секретные данные. Бот не может восстановить доступ к аккаунту."),
    ]),
    "email": ("Не приходит код подтверждения email", [
        ("Проверить почту", "Проверьте адрес и папки «Спам» и «Рассылки»."),
        ("Повторить отправку", "Запросите письмо повторно на сайте. Бот не отправляет и не проверяет коды."),
        ("Безопасность", "Не присылайте код подтверждения в Telegram чат с ботом."),
    ]),
    "telegram": ("Не работает привязка Telegram", [
        ("Проверить профиль", "Войдите в нужный аккаунт Luna Market и подключите Telegram в настройках профиля."),
        ("Повторить проверку", "Вернитесь в бота и откройте «📦 Мои заказы». Если привязка не распознаётся, проверьте, что выбран нужный аккаунт сайта."),
    ]),
}


def problems_keyboard():
    rows = [[InlineKeyboardButton(text=title, callback_data=f"sup:problem:{key}")] for key, (title, _) in PROBLEMS.items()]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="sup:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def problem_steps_keyboard(problem_id, step, total):
    rows = []
    if step + 1 < total:
        rows.append([InlineKeyboardButton(text="Продолжить ➡️", callback_data=f"sup:step:{problem_id}:{step + 1}")])
    if step > 0:
        rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"sup:step:{problem_id}:{step - 1}")])
    rows.append([InlineKeyboardButton(text="🛠 К списку проблем", callback_data="sup:problems")])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню поддержки", callback_data="sup:home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
