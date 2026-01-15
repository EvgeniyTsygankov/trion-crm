"""Точка входа для запуска Telegram-бота CRM.

Импортирует объект bot и модули с хендлерами, чтобы зарегистрировать все
@bot.message_handler, затем запускает бесконечный long polling.
"""

import importlib

from .bot import bot
from .logger import logger

HANDLER_MODULES = [
    "telegram_bot.handlers_auth",
    "telegram_bot.handlers_clients",
    "telegram_bot.handlers_orders",
    "telegram_bot.handlers_purchases",
]


def load_handlers() -> None:
    """Импортирует все модули с хендлерами (@bot.message_handler)."""
    for module in HANDLER_MODULES:
        importlib.import_module(module)
    logger.info("Handlers loaded: %s", ", ".join(HANDLER_MODULES))


def main() -> None:
    """Точка входа для запуска бота."""
    load_handlers()
    logger.info("Bot started, polling...")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
