"""Скрипт запуска pytest тестов для Django проекта в pre-push хуке.

Этот скрипт выполняет запуск тестов перед отправкой изменений в репозиторий
(git push). Если тесты не проходят, push блокируется, предотвращая попадание
непротестированного кода в основную ветку.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def main() -> int:
    """Основная функция запуска тестов.

    Процесс выполнения:
    1. Определяет абсолютный путь к директории backend проекта
    2. Устанавливает обязательные переменные окружения Django
    3. Меняет рабочую директорию на backend для корректных импортов
    4. Добавляет backend в PYTHONPATH для доступа к модулям Django
    5. Запускает pytest с параметром детализированного вывода (-vv)
    """
    backend_dir = Path(__file__).resolve().parents[1]
    os.environ.setdefault('DEBUG', 'True')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tech_support.settings')

    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))

    return pytest.main(['-vv'])


if __name__ == "__main__":
    raise SystemExit(main())
