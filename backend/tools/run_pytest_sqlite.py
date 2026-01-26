"""Модуль для запуска pytest с использованием SQLite.

Скрипт настраивает окружение для запуска тестов с базой данных SQLite,
что обеспечивает быстрые и изолированные тесты без необходимости внешней БД.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def main() -> int:
    """Главная функция запуска pytest с SQLite.

    Настраивает окружение Django для использования
    SQLite (установкой DEBUG=True) и запускает pytest с подробным выводом.

    Код возврата pytest:
        - 0: Все тесты прошли успешно
        - 1: Некоторые тесты не прошли
        - 2: Ошибка прерывания тестов (KeyboardInterrupt)
        - 3: Внутренняя ошибка pytest
        - 4: Ошибка использования командной строки pytest
        - 5: Не найдено ни одного теста

    Флаг DEBUG=True заставляет settings.py использовать SQLite
    вместо PostgreSQL.
    """
    backend_dir = Path(__file__).resolve().parents[1]

    os.environ.setdefault('DEBUG', 'True')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tech_support.settings')

    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))

    return pytest.main(['-vv'])


if __name__ == '__main__':
    raise SystemExit(main())
