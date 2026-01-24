"""Кастомные обработчики HTTP-ошибок."""

from django.shortcuts import render


def csrf_failure(request, reason=''):
    """Обработчик ошибки CSRF-защиты."""
    return render(request, 'pages_errors/403_csrf.html', status=403)


def permission_denied(request, exception=None):
    """Обработчик ошибки 403 Forbidden - Запрос отклонён."""
    return render(request, "pages_errors/403.html", status=403)


def page_not_found(request, exception=None):
    """Обработчик ошибки 404 NOT_FOUND - Страница не найдена."""
    return render(request, 'pages_errors/404.html', status=404)


def server_error(request):
    """Обработчик ошибки 500 INTERNAL_SERVER_ERROR - Ошибка сервера."""
    return render(request, "pages_errors/500.html", status=500)
