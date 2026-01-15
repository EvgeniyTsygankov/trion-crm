"""Тесты для моделей CRM-системы (проверка строковых представлений и метаданных).

Этот файл содержит тесты для проверки:
1. Методов __str__() всех моделей
2. Верных настроек verbose_name и verbose_name_plural
3. Вспомогательных текстов (help_text) для полей
"""

from decimal import Decimal

import pytest

from crm.models import (
    Category,
    Client,
    Order,
    Purchase,
    PurchaseStatus,
    Service,
)


@pytest.mark.django_db
def test_client_str():
    """Проверяет строковое представление модели Client."""
    client = Client.objects.create(
        client_name='Иван',
        mobile_phone='+79990000012',
        entity_type='FL',
    )
    assert (
        str(client) == 'Иван, тел.+79990000012'
    ), '__str__ клиента должен возвращать "Имя, тел.номер"'


@pytest.mark.django_db
def test_category_str():
    """Проверяет строковое представление модели Category."""
    category = Category.objects.create(
        title='Тестовая категория',
        slug='test-category',
    )
    assert (
        str(category) == 'Тестовая категория'
    ), '__str__ категории должен возвращать title'


@pytest.mark.django_db
def test_service_str():
    """Проверяет строковое представление модели Service."""
    category = Category.objects.create(
        title='Услуги',
        slug='services',
    )
    service = Service.objects.create(
        category=category,
        service_name='Настройка ПО',
        amount=Decimal('500.00'),
    )
    assert (
        str(service) == 'Настройка ПО'
    ), '__str__ услуги должен возвращать service_name'


@pytest.mark.django_db
def test_order_str_and_meta(crm_data):
    """Проверяет строковое представление и метаданные модели Order.

    Использует фикстуру crm_data для получения готового заказа.
    """
    order = crm_data['order1']
    assert 'Заказ' in str(
        order
    ), '__str__ заказа должен содержать слово "Заказ"'
    assert order._meta.verbose_name == 'Заказ'
    assert order._meta.verbose_name_plural == 'Заказы'


@pytest.mark.django_db
def test_client_meta():
    """Проверяет метаданные модели Client (verbose_name, help_text)."""
    client = Client(
        client_name='Тест',
        mobile_phone='+79990000013',
        entity_type='FL',
    )
    meta = client._meta
    # Проверка отображаемых имен
    assert meta.verbose_name == 'Клиент'
    assert meta.verbose_name_plural == 'Клиенты'
    # Проверка подсказки для поля номера телефона
    field = meta.get_field('mobile_phone')
    assert field.verbose_name == 'Мобильный телефон'
    assert 'формате +79998887766' in (
        field.help_text or ''
    ), 'help_text для mobile_phone должен подсказывать формат ввода'


@pytest.mark.django_db
def test_service_meta():
    """Проверяет метаданные модели Service."""
    category = Category.objects.create(
        title='Категория',
        slug='category',
    )
    service = Service.objects.create(
        category=category,
        service_name='Тестовая услуга',
        amount=Decimal('1000.00'),
    )
    meta = service._meta
    assert meta.verbose_name == 'Услуга'
    assert meta.verbose_name_plural == 'Услуги'
    # Проверка verbose_name для полей
    amount_field = meta.get_field('amount')
    assert amount_field.verbose_name == 'Базовая стоимость'


@pytest.mark.django_db
def test_category_meta():
    """Проверяет метаданные модели Category."""
    category = Category.objects.create(
        title='Категория',
        slug='test',
    )
    meta = category._meta
    assert meta.verbose_name == 'Категория'
    assert meta.verbose_name_plural == 'Категории'
    slug_field = meta.get_field('slug')
    assert slug_field.verbose_name == 'Слаг'


def test_order_field_meta():
    """Проверяет метаданные полей модели Order без создания объекта."""
    meta = Order._meta

    accepted_field = meta.get_field('accepted_equipment')
    assert accepted_field.verbose_name == 'Принятое оборудование'
    assert 'Наименование оборудования' in (accepted_field.help_text or ''), (
        'help_text для accepted_equipment должен подсказать, '
        'что это наименование оборудования'
    )

    detail_field = meta.get_field('detail')
    assert detail_field.verbose_name == 'Детали заказа'
    assert 'Описание неисправности' in (
        detail_field.help_text or ''
    ), 'help_text для detail должен подсказать,что это описание неисправности'


@pytest.mark.django_db
def test_purchase_meta():
    """Проверяет метаданные модели Purchase."""
    purchase = Purchase.objects.create(
        store='DNS',
        detail='Жёсткий диск',
        status=PurchaseStatus.AWAITING_RECEIPT,
    )
    meta = purchase._meta
    assert meta.verbose_name == 'Покупка'
    assert meta.verbose_name_plural == 'Покупки'


@pytest.mark.django_db
def test_purchase_status_choices():
    """Проверяет, что у модели Purchase есть корректные статусы."""
    purchase = Purchase.objects.create(
        store='Магазин',
        detail='Деталь',
        status=PurchaseStatus.AWAITING_RECEIPT,
    )
    status_field = purchase._meta.get_field('status')
    expected_codes = [
        PurchaseStatus.AWAITING_RECEIPT,
        PurchaseStatus.RECEIVED,
        PurchaseStatus.INSTALLED,
    ]
    actual_codes = [choice[0] for choice in status_field.choices]
    for expected in expected_codes:
        assert (
            expected in actual_codes
        ), f'Статус "{expected}" должен быть в choices модели Purchase'
    # Проверяем читаемое название статуса через TextChoices.label
    assert (
        purchase.get_status_display() == PurchaseStatus.AWAITING_RECEIPT.label
    ), (
        'get_status_display() должен возвращать label из PurchaseStatus '
        '(ожидает получения)'
    )
