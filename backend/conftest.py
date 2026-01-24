"""Тестовые фикстуры для CRM-системы.

Создаёт готовый набор тестовых данных:
- 2 клиента (ФЛ и ЮЛ)
- Категорию и 2 услуги
- 3 заказа с разными статусами
- 4 покупки (3 привязанных, 1 нет)
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from crm.models import Category, Client, Order, Purchase, Service

User = get_user_model()


def get_results(data):
    """Извлекает список объектов из ответа API (с пагинацией и без)."""
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    return data


def get_jwt_token(user):
    """Создаёт JWT access-токен для пользователя."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def create_test_user():
    """Создаёт тестового пользователя."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',  # noqa
    )


def setup_api_client_with_auth(api_client, user):
    """Настраивает APIClient с JWT-аутентификацией."""
    token = get_jwt_token(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client


def teardown_api_client_auth(api_client):
    """Сбрасывает авторизацию APIClient."""
    api_client.credentials()


@pytest.fixture
def api_client():
    """Базовый DRF APIClient (без авторизации)."""
    return APIClient()


@pytest.fixture
def api_user(db):
    """Пользователь для авторизации в API."""
    return create_test_user()


@pytest.fixture
def api_client_auth(api_client, api_user):
    """Возвращает API-клиент с настроенной JWT-аутентификацией."""
    setup_api_client_with_auth(api_client, api_user)
    try:
        yield api_client
    finally:
        teardown_api_client_auth(api_client)


def create_crm_orders_and_purchases():
    """Создаёт тестовые данные для клиентов, заказов, услуг и покупок.

    Возвращает словарь с объектами:
      client1, client2, category, service1, service2,
      order1, order2, order3,
      purchase1, purchase2, purchase3, purchase_orphan.
    """
    client1 = Client.objects.create(
        client_name='Иван Иванов',
        mobile_phone='+79990000001',
        entity_type='FL',
        company='',
        address='',
    )
    client2 = Client.objects.create(
        client_name='ООО Ромашка',
        mobile_phone='+79990000002',
        entity_type='UL',
        company='ООО Ромашка',
        address='ул. Пушкина, д. 1',
    )

    category = Category.objects.create(
        title='Диагностика',
        slug='diagnostics',
    )

    service1 = Service.objects.create(
        category=category,
        service_name='Диагностика ноутбука',
        amount=Decimal('1000.00'),
    )
    service2 = Service.objects.create(
        category=category,
        service_name='Чистка от пыли',
        amount=Decimal('500.00'),
    )

    order1 = Order.objects.create(
        number=101,
        client=client1,
        accepted_equipment='Ноутбук Lenovo',
        detail='Не включается',
        advance=Decimal('300.00'),
        paid=Decimal('0.00'),
        status='in_working',
    )
    order1.services.set([service1, service2])

    order2 = Order.objects.create(
        number=102,
        client=client1,
        accepted_equipment='Монитор Samsung',
        detail='Мерцает подсветка',
        advance=Decimal('0.00'),
        paid=Decimal('200.00'),
        status='completed',
    )
    order2.services.set([service1])

    order3 = Order.objects.create(
        number=103,
        client=client2,
        accepted_equipment='Принтер HP',
        detail='Застревает бумага',
        advance=Decimal('200.00'),
        paid=Decimal('0.00'),
        status='under_approval',
    )
    order3.services.set([])

    purchase1 = Purchase.objects.create(
        order=order1,
        store='DNS',
        detail='Жёсткий диск 1Тб',
        cost=Decimal('5000.00'),
        status='delivery_expected',
    )
    purchase2 = Purchase.objects.create(
        order=order1,
        store='Citilink',
        detail='Память DDR4 8Гб',
        cost='4000',
        status='received',
    )
    purchase3 = Purchase.objects.create(
        order=order2,
        store='DNS',
        detail='Шлейф матрицы',
        cost='1000',
        status='installed',
    )
    purchase_orphan = Purchase.objects.create(
        order=None,
        store='DNS',
        detail='Не привязано к заказу',
        cost=Decimal('0.00'),
        status='delivery_expected',
    )

    return {
        'client1': client1,
        'client2': client2,
        'category': category,
        'service1': service1,
        'service2': service2,
        'order1': order1,
        'order2': order2,
        'order3': order3,
        'purchase1': purchase1,
        'purchase2': purchase2,
        'purchase3': purchase3,
        'purchase_orphan': purchase_orphan,
    }


@pytest.fixture
def crm_data(db):
    """Фикстура с тестовыми данными CRM."""
    return create_crm_orders_and_purchases()
