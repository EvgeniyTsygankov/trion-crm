"""Модуль для проверки миграций Django.

Скрипт проверяет, есть ли непрогнанные миграции в проекте Django.
Используется в CI/CD для предотвращения развертывания без актуальных миграций.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import django
from django.core.management import call_command


def main() -> int:
    """Главная функция проверки миграций.

    Настраивает окружение Django и проверяет наличие непрогнанных миграций
    с помощью команды `makemigrations --check --dry-run`.

    Код возврата:
        - 0: Миграции в порядке (нет непрогнанных изменений моделей)
        - 1: Обнаружены непрогнанные миграции (или ошибка)
    """
    backend_dir = Path(__file__).resolve().parents[1]
    os.environ.setdefault('DEBUG', 'True')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tech_support.settings')

    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))

    django.setup()

    call_command('makemigrations', '--check', '--dry-run', verbosity=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
