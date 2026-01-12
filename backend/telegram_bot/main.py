"""
Точка входа для запуска Telegram-бота CRM.

Импортирует объект bot и модули с хендлерами, чтобы зарегистрировать все
@bot.message_handler, затем запускает бесконечный long polling.
"""

from .bot import bot


def main():
    """Точка входа для запуска бота."""
    bot.infinity_polling(skip_pending=True)


if __name__ == '__main__':
    main()
