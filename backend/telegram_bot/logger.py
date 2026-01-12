"""Конфигурация логирования Telegram-бота CRM."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 1. Определяем путь к папке logs относительно этого файла
LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'

# 2. Создаем папку logs если она не существует
LOG_DIR.mkdir(exist_ok=True)

# 3. Определяем путь к файлу лога внутри папки logs
LOG_FILE = LOG_DIR / 'main.log'

# 4. Создаем логгер
logger = logging.getLogger('telegram_bot')
logger.setLevel(logging.INFO)

# 5. Очищаем существующие обработчики (чтобы избежать дублирования)
if logger.hasHandlers():
    logger.handlers.clear()

# 6. Создаем RotatingFileHandler
handler = RotatingFileHandler(
    LOG_FILE, maxBytes=50_000_000, backupCount=3, encoding='utf-8'  # 50 MB
)

# 7. Настраиваем форматтер
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
handler.setFormatter(formatter)

# 8. Добавляем обработчик к логгеру
logger.addHandler(handler)

# 9. Отключаем propagation
logger.propagate = False

# 10. Добавляем вывод в консоль для удобства разработки
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
