"""Тесты бизнес-логики CRM-системы.

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
def test_order_services_total_and_duty(crm_data):
    """Проверяет вычисления.

    - services_total: сумма услуг заказа;
    - purchases_total: сумма покупок заказа;
    - total_amount: общая сумма для клиента = services_total + purchases_total;
    - duty: долг клиента с учётом аванса.

    Для order1:
    - service1 = 1000
    - service2 = 500
    - services_total = service1 + service2 = 1500
    - purchase1 = 5000
    - purchase2 = 4000
    - purchases_total = purchase1 + purchase2 = 9000
    - total_amount = services_total + purchases_total = 10500
    - advance = 300.00
    - paid = 0.00
    """
    order = crm_data['order1']
    assert order.services_total == Decimal(
        '1500.00'
    ), 'services_total должен быть равен сумме стоимости услуг заказа'
    assert order.purchases_total == Decimal(
        '9000.00'
    ), 'purchases_total должен быть равен сумме стоимости покупок заказа'
    assert order.total_amount == Decimal(
        '10500.00'
    ), 'total_amount должен быть равен сумме услуг и покупок заказа'
    # duty = 10500 - 300 = 10200
    assert order.duty == Decimal(
        '10200.00'
    ), 'duty должен равняться total_amount - advance'


@pytest.mark.django_db
def test_order_duty_with_paid(crm_data):
    """Проверяет расчет долга (duty) при наличии оплаты (paid).

    Для order2:
    - service1 = 1000
    - purchase3 = 1000
    - total_amount = service1 + purchase3 = 2000
    - advance = 0.00
    - paid = 200.00
    """
    order = crm_data['order2']
    # duty = 2000 - 200 = 1800
    assert order.duty == Decimal(
        '1800.00'
    ), 'duty должен равняться total_amount - paid'


@pytest.mark.django_db
def test_order_services_total_without_services():
    """Если у заказа нет услуг, services_total должен быть 0."""
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
    assert order.services_total == Decimal(
        '0.00'
    ), 'services_total для заказа без услуг должен быть 0'
    assert order.purchases_total == Decimal(
        '0.00'
    ), 'purchases_total для заказа без покупок должен быть 0'
    assert order.duty == Decimal(
        '0.00'
    ), 'duty для заказа без услуг, без покупок и без аванса должен быть 0'


@pytest.mark.django_db
def test_client_total_duty_aggregates_orders(crm_data):
    """Проверяет, что Client.total_duty агрегирует все заказы клиента.

    Для client1:
    order1:
        services_total = 1000 + 500 = 1500
        purchases_total = 5000 + 4000 = 9000
        total_amount = services_total + purchases_total = 10500
        advance = 300
        paid = 0
        duty = total_amount - advance - paid = 10200

    order2:
        services_total = service1 = 1000
        purchases_total = purchase3 = 1000
        total_amount = services_total + purchases_total = 2000
        advance = 0
        paid = 200
        duty = total_amount - advance - paid = 1800
    """
    client1 = crm_data['client1']
    # total_duty = 10200 + 1800 = 12000
    assert client1.total_duty == Decimal(
        '12000.00'
    ), 'total_duty клиента должен равняться сумме долгов по всем его заказам'


@pytest.mark.django_db
def test_order_queryset_total_duty(crm_data):
    """OrderQuerySet.total_duty должен корректно считать общий долг.

    Для client1:
    order1:
        services_total = 1000 + 500 = 1500
        purchases_total = 5000 + 4000 = 9000
        total_amount = services_total + purchases_total = 10500
        advance = 300
        paid = 0
        duty = total_amount - advance - paid = 10200

    order2:
        services_total = service1 = 1000
        purchases_total = purchase3 = 1000
        total_amount = services_total + purchases_total = 2000
        advance = 0
        paid = 200
        duty = total_amount - advance - paid = 1800

    client1.total_duty = 12000

    Для client2:
        services_total = service1 = 1000
    order3:
        services_total = 0
        purchases_total = 0
        total_amount = 0
        advance = 200
        paid = 0
        duty = total_amount - advance - paid = -200

    client2.total_duty = -200
    """
    total = Order.objects.all().total_duty()
    # total_duty= client1.total_duty + client2.total_duty = 12000 - 200 = 11800
    assert total == Decimal('11800.00'), (
        'OrderQuerySet.total_duty должен возвращать сумму '
        '(total_amount - advance - paid) по всем заказам выборки'
    )


@pytest.mark.django_db
def test_order_queryset_total_duty_includes_paid(crm_data):
    """Проверяет, что метод total_duty() менеджера корректно учитывает оплаты.

    Проверяет, что метод total_duty() менеджера Order.objects.all()
    корректно учитывает оплаты (paid) при расчете общего долга.

    Исходные данные:
    order1:
        services_total = 1000 + 500 = 1500
        purchases_total = 5000 + 4000 = 9000
        total_amount = services_total + purchases_total = 10500
        advance = 300
        paid = 0
        duty = total_amount - advance - paid = 10200

    order2:
        services_total = servicel = 1000
        purchases_total = purchase3 = 1000
        total_amount = services_total + purchases_total = 2000
        advance = 0
        paid = 200
        duty = total_amount - advance - paid = 1800

    order3:
        advance = 200

    Тест:
    - Для order2.paid обновляем значение с 200 на 1800
    - Новый duty для order2: 2000 - 1800 = 200.00
    - Новый общий долг total_duty = 10200 + 200 - 200 = 10200.00

    Проверяем, что total_duty() возвращает 10200.00.
    """
    order2 = crm_data['order2']
    order2.paid = Decimal('1800.00')
    order2.save(update_fields=['paid'])
    total = Order.objects.all().total_duty()
    assert total == Decimal('10200.00'), (
        f'Ожидается общий долг 10200.00 после оплаты 1800.00 по order2, '
        f'получено {total}'
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
    assert (
        str(order.number) in order.code
    ), 'Числовой номер заказа должен входить в строку code'
    assert 'Заказ' in str(
        order
    ), '__str__ заказа должен содержать слово "Заказ" и код заказа'
