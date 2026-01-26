"""Скрипт запуска pytest тестов для Django проекта в pre-push хуке.

Устанавливает DEBUG=True и запускает тесты из backend директории.
Используется как проверка перед push'ем в репозиторий.
"""

from __future__ import annotations

import os

import pytest


def main() -> int:
    """Запускает pytest тесты с DEBUG=True."""
    os.environ.setdefault('DEBUG', 'True')
    return pytest.main(['-vv'])


if __name__ == "__main__":
    raise SystemExit(main())
