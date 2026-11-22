# 🌙 Luna Market Bot

**Luna Market Bot** — Telegram-бот интернет-магазина [Luna Market](https://luna-market.onrender.com/), написанный на **Python и aiogram 3**. Бот использует Express API магазина для каталога, привязки аккаунта и просмотра заказов.

**[🤖 Открыть @LunaMarketGameBot](https://t.me/LunaMarketGameBot)** · **[🌐 Открыть магазин](https://luna-market.onrender.com/)** · **[💻 Репозиторий сайта и API](https://github.com/theKywer/store-site)**

> Учебный проект. Покупки и оплата в Luna Market демонстрационные; настоящие платежи не обрабатываются.

## ✨ Возможности

- `/start` и `/help`, удобное меню с кнопками.
- **🎮 Каталог** — просмотр игр и навигация по карточкам.
- **🔎 Поиск** — поиск игр через интерфейс бота.
- **📦 Мои заказы** — просмотр истории заказов пользователя после привязки аккаунта.
- **🔗 Привязка аккаунта** — безопасное подключение через одноразовую ссылку из профиля сайта.
- **💬 Поддержка** — автоматизированный справочный раздел, ответы на частые вопросы и сценарии самопомощи.
- **🔔 Уведомления о заказах** — события покупки и изменения статуса отправляются через интеграцию Express с Telegram; уведомления настраиваются в профиле магазина.

## 🛠 Технологии

- Python 3
- [aiogram 3](https://docs.aiogram.dev/)
- [httpx](https://www.python-httpx.org/) — HTTP-запросы к API
- `python-dotenv` — локальные переменные окружения
- Telegram Bot API, асинхронный long polling
- Railway — развёртывание бота

## 🔗 Как это устроено

```text
Telegram → Luna Market Bot (Python / aiogram, Railway)
                    │
                    │ HTTPS + X-Telegram-Bot-Secret
                    ▼
             Express API (Render) ──► PostgreSQL (Neon)
                    ▲
                    │ HTTPS
              React-сайт (Render)
```

Бот не подключается к базе данных напрямую. Доступ к заказам и операциям привязки проходит через защищённые маршруты Express. `TELEGRAM_BRIDGE_SECRET` хранится отдельно от токена Telegram и должен совпадать на стороне Python и Express.

## 📁 Структура

```text
luna-market-bot/
├── bot/
│   ├── handlers.py          # Каталог, поиск и основное меню
│   ├── orders.py            # Интерфейс истории заказов
│   ├── telegram_link.py     # Привязка через deep link
│   ├── services/            # Запросы к Express API
│   └── support/             # Автоматизированная поддержка
├── main.py                  # Запуск Dispatcher и polling
├── requirements.txt
└── README.md
```

## 🛡 Безопасность

- История заказов доступна только после подтверждённой привязки Telegram к аккаунту сайта.


## 📌 Статус

Бот развёрнут на Railway и интегрирован с облачным API Luna Market. Проект создан в образовательных целях и развивается вместе с магазином.

## 👨‍💻 Автор

[theKywer](https://github.com/theKywer)

---

Luna Market Bot © 2026