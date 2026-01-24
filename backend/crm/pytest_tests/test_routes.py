"""Модуль для тестирования URL-маршрутов Django приложения CRM.

Этот файл содержит тесты, которые проверяют корректность настройки
URL-маршрутов:
1. Соответствие имен маршрутов фактическим URL
2. Корректное разрешение URL в соответствующие представления (views)
3. Доступность эндпоинтов (отсутствие 404 ошибок)

Используется подход параметризованного тестирования для эффективной проверки
множества маршрутов с минимальным дублированием кода.
"""

from http import HTTPStatus

import pytest
from django.urls import resolve, reverse

from crm.views import (
    ClientCreateView,
    ClientDeleteView,
    ClientDetailView,
    ClientListView,
    ClientUpdateView,
    HomeView,
    OrderCreateView,
    OrderDeleteView,
    OrderDetailView,
    OrderListView,
    OrderUpdateView,
    PurchaseCreateView,
    PurchaseDeleteView,
    PurchaseDetailView,
    PurchaseListView,
    PurchaseUpdateView,
    ServiceCreateView,
    ServiceDeleteView,
    ServiceListView,
    ServiceUpdateView,
)

# Маршруты, не требующие pk
ROUTES_NO_PK = [
    ('home', HomeView),
    ('client_list', ClientListView),
    ('client_create', ClientCreateView),
    ('service_list', ServiceListView),
    ('service_create', ServiceCreateView),
    ('order_list', OrderListView),
    ('order_create', OrderCreateView),
    ('purchase_list', PurchaseListView),
    ('purchase_create', PurchaseCreateView),
]

# Маршруты, требующие pk.
# Третий элемент — ключ объекта в фикстуре crm_data.
ROUTES_WITH_PK = [
    ('client_detail', ClientDetailView, 'client1'),
    ('client_edit', ClientUpdateView, 'client1'),
    ('client_delete', ClientDeleteView, 'client1'),
    ('service_edit', ServiceUpdateView, 'service1'),
    ('service_delete', ServiceDeleteView, 'service1'),
    ('order_detail', OrderDetailView, 'order1'),
    ('order_edit', OrderUpdateView, 'order1'),
    ('order_delete', OrderDeleteView, 'order1'),
    ('purchase_detail', PurchaseDetailView, 'purchase1'),
    ('purchase_edit', PurchaseUpdateView, 'purchase1'),
    ('purchase_delete', PurchaseDeleteView, 'purchase1'),
]


@pytest.mark.parametrize(('url_name', 'view_class'), ROUTES_NO_PK)
def test_routes_without_pk_resolve_and_not_404(client, url_name, view_class):
    """Проверяет, что маршруты без pk корректно реверсятся и разрешаются.

    Тестирует три аспекта для маршрутов без идентификатора объекта:
    1. Корректность генерации URL по имени маршрута (reverse)
    2. Правильное разрешение URL в соответствующее представление (resolve)
    3. Доступность эндпоинта (отсутствие ошибки 404 при GET-запросе)
    """
    # reverse не должен упасть с NoReverseMatch
    url = reverse(url_name)

    # resolve должен вернуть правильный класс представления
    resolver = resolve(url)
    assert resolver.func.view_class is view_class, (
        f'Маршрут "{url_name}" должен использовать представление '
        f'{view_class.__name__}'
    )

    # GET-запрос не должен вернуть 404(может быть 200,302 при редиректе и т.п.)
    response = client.get(url)
    assert (
        response.status_code != HTTPStatus.NOT_FOUND
    ), f'GET {url!r} для маршрута "{url_name}" не должен возвращать 404'


@pytest.mark.django_db
@pytest.mark.parametrize(("url_name", "view_class", "obj_key"), ROUTES_WITH_PK)
def test_routes_with_pk_resolve_and_not_404(
    client, crm_data, url_name, view_class, obj_key
):
    """Проверяет, что маршруты с pk корректно реверсятся и разрешаются.

    Тестирует три аспекта для маршрутов с идентификатором объекта:
    1. Корректность генерации URL с передачей pk
    2. Правильное разрешение URL в соответствующее представление
    3. Доступность эндпоинта для существующего объекта.
    """
    obj = crm_data[obj_key]

    # reverse с pk существующего объекта
    url = reverse(url_name, kwargs={'pk': obj.pk})

    # resolve должен вернуть правильный класс представления
    resolver = resolve(url)
    assert resolver.func.view_class is view_class, (
        f'Маршрут "{url_name}" должен использовать представление '
        f'{view_class.__name__}'
    )

    # GET-запрос не должен возвращать 404
    response = client.get(url)
    assert response.status_code != HTTPStatus.NOT_FOUND, (
        f'GET {url!r} для маршрута "{url_name}" и pk={obj.pk} не должен '
        f'возвращать 404'
    )
