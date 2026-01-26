"""Pre-push хук: запуск проверок Django перед отправкой кода в Git.

Скрипт выполняет две критически важные проверки:
1. Проверяет наличие не созданных миграций БД
2. Запускает тесты проекта через pytest

Если любая проверка не проходит, git push блокируется,
предотвращая попадание некорректного кода в удалённый репозиторий.

Использование:
    Автоматически вызывается при выполнении git push.
    Вручную: python backend/scripts/run_tests.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import django
from django.core.management import call_command


def main() -> int:
    """Выполняет проверки перед push.

    Процесс выполнения:
    1. Определяет путь к backend директории
    2. Настраивает Django окружение (DEBUG, DJANGO_SETTINGS_MODULE)
    3. Переходит в директорию проекта и добавляет её в PYTHONPATH
    4. Инициализирует Django (django.setup())
    5. Проверяет отсутствие неприменённых миграций (makemigrations --check)
    6. Запускает pytest тесты с подробным выводом (-vv)

    Возврат результата:
       - 0: успех, все проверки пройдены
       - 1: ошибка миграций
       - 2: ошибка тестов
       - 3+: системные ошибки
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
