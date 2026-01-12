"""
Тесты бизнес-логики CRM-системы.

Этот файл содержит тесты для проверки:
1. Валидации данных (номера телефонов, обязательных полей)
2. Вычисления бизнес-показателей (стоимость заказов, долги)
3. Работы методов моделей (clean, свойства total_price/duty)
4. Кастомных QuerySet методов (агрегация по клиентам/заказам)
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from crm.models import Client, Order, OrderStatus
from crm.validators import phone_validator, validate_company_for_legal


@pytest.mark.django_db
def test_phone_validator_valid():
    """Корректный номер телефона проходит валидацию."""
    phone_validator('+79998887766')


@pytest.mark.django_db
def test_phone_validator_invalid():
    """Некорректный номер телефона (без +7) вызывает ValidationError."""
    with pytest.raises(ValidationError):
        phone_validator('89998887766')


@pytest.mark.django_db
def test_validate_company_for_legal_requires_company():
    """Для юридического лица поле company обязательно."""
    with pytest.raises(ValidationError):
        validate_company_for_legal('', 'UL')


@pytest.mark.django_db
def test_validate_company_for_legal_for_fl_no_company_ok():
    """Для физического лица пустое company допустимо."""
    validate_company_for_legal('', 'FL')


@pytest.mark.django_db
def test_client_clean_company_required_for_legal():
    """Client.clean() должен требовать company для UL."""
    client = Client(
        client_name='ООО Ромашка',
        mobile_phone='+79990000003',
        entity_type='UL',
        company='',
    )
    with pytest.raises(ValidationError):
        client.full_clean()


@pytest.mark.django_db
def test_order_total_price_and_duty(crm_data):
    """Проверяет вычисление total_price и duty заказа."""
    order = crm_data['order1']
    # service1 = 1000, service2 = 500, итого 1500
    assert order.total_price == Decimal(
        '1500.00'
    ), 'total_price должен быть равен сумме стоимости услуг заказа'
    # advance = 300, duty = 1500 - 300 = 1200
    assert order.duty == Decimal(
        '1200.00'
    ), 'duty должен равняться total_price - advance'


@pytest.mark.django_db
def test_order_total_price_without_services():
    """Если у заказа нет услуг, total_price должен быть 0."""
    client = Client.objects.create(
        client_name='Тест',
        mobile_phone='+79990000010',
        entity_type='FL',
    )
    order = Order.objects.create(
        number=201,
        client=client,
        accepted_equipment='Тестовое устройство',
        detail='Тестовое описание',
        advance=Decimal('0.00'),
        status=OrderStatus.IN_WORKING,
    )
    assert order.total_price == Decimal(
        '0.00'
    ), 'total_price для заказа без услуг должен быть 0'
    assert order.duty == Decimal(
        '0.00'
    ), 'duty для заказа без услуг и без аванса должен быть 0'


@pytest.mark.django_db
def test_client_total_duty_aggregates_orders(crm_data):
    """Проверяет, что Client.total_duty агрегирует все заказы клиента."""
    client1 = crm_data['client1']

    # Для client1:
    # order1: services 1000+500=1500, advance 300 → duty 1200
    # order2: services 1000, advance 0 → duty 1000
    # Итого 2200
    assert client1.total_duty == Decimal(
        '2200.00'
    ), 'total_duty клиента должен равняться сумме долгов по всем его заказам'


@pytest.mark.django_db
def test_order_queryset_total_duty(crm_data):
    """OrderQuerySet.total_duty должен корректно считать общий долг."""
    from crm.models import Order

    total = Order.objects.all().total_duty()
    # client1 (order1 + order2) = 1200 + 1000 = 2200
    # client2 (order3): services_sum=0, advance=200 → duty=-200
    # Итого: 2200 + (-200) = 2000
    assert total == Decimal('2000.00'), (
        'OrderQuerySet.total_duty должен возвращать сумму '
        '(services_sum - advance) по всем заказам выборки'
    )


@pytest.mark.django_db
def test_order_code_format():
    """Проверяет формат кода заказа (code)."""
    client = Client.objects.create(
        client_name='Тест',
        mobile_phone='+79990000011',
        entity_type='FL',
    )
    order = Order.objects.create(
        number=7,
        client=client,
        accepted_equipment='Телефон',
        detail='Разбит экран',
        advance=Decimal('0.00'),
    )
    # Для проверки не завязаны на конкретные константы,
    # но можно проверить, что код содержит номер и префикс.
    assert (
        str(order.number) in order.code
    ), 'Числовой номер заказа должен входить в строку code'
    assert 'Заказ' in str(
        order
    ), '__str__ заказа должен содержать слово "Заказ" и код заказа'
