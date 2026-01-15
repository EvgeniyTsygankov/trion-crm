"""Конфигурация Telegram-бота CRM, читаемая из окружения (.env).

Содержит:
- базовый URL API (API_BASE_URL);
- токен Telegram-бота (TELEGRAM_BOT_TOKEN);
- список разрешённых chat_id (TELEGRAM_ALLOWED_CHAT_IDS),
  используемый для ограничения доступа.

Файл описывает только параметры окружения и не содержит бизнес-логики
или прикладных констант бота.
"""

import os

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    'API_BASE_URL',
)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

allowed_ids_raw = os.getenv('TELEGRAM_ALLOWED_CHAT_IDS', '')
if allowed_ids_raw:
    TELEGRAM_ALLOWED_CHAT_IDS = {
        int(part.strip())
        for part in allowed_ids_raw.split(',')
        if part.strip()
    }
else:
    TELEGRAM_ALLOWED_CHAT_IDS = set()
