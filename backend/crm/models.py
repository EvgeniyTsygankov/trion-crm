"""Модели для приложения CRM-системы."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Sum
from sequences import get_next_value

from .constants import (
    MAX_LENGTH_ADDRESS,
    MAX_LENGTH_COMPANY_NAME,
    MAX_LENGTH_COMPONENT_DETAIL,
    MAX_LENGTH_COMPONENT_FIELD,
    MAX_LENGTH_ENTITY_TYPE,
    MAX_LENGTH_MOBILE_PHONE,
    MAX_LENGTH_NAME_CLIENT,
    MAX_LENGTH_NAME_SHOP,
    MAX_LENGTH_OF_DETAIL_SHOP,
    MAX_LENGTH_OF_NAME_CATEGORY,
    MAX_LENGTH_OF_NAME_SERVICE,
    MAX_LENGTH_OF_SLUG,
    MAX_LENGTH_ORDER_STATUS,
    MAX_LENGTH_PURCHASE_STATUS,
    MONEY_DECIMAL_PLACES,
    MONEY_MAX_DIGITS,
    ORDER_CODE_PAD,
    ORDER_CODE_PREFIX,
    ORDER_SEQUENCE_NAME,
)
from .validators import phone_validator, validate_company_for_legal

User = get_user_model()


class EntityType(models.TextChoices):
    """Выбор вида клиента."""

    FL = 'FL', 'физ'
    UL = 'UL', 'юр'


class Client(models.Model):
    """Класс создания клиента."""

    client_name = models.CharField(
        verbose_name='Имя клиента', max_length=MAX_LENGTH_NAME_CLIENT
    )
    mobile_phone = models.CharField(
        verbose_name='Мобильный телефон',
        max_length=MAX_LENGTH_MOBILE_PHONE,
        validators=[phone_validator],
        help_text='Введите номер телефона в формате +79998887766',
        unique=True,
    )
    entity_type = models.CharField(
        verbose_name='Тип лица',
        choices=EntityType.choices,
        default=EntityType.UL,
        max_length=MAX_LENGTH_ENTITY_TYPE,
    )
    company = models.CharField(
        verbose_name='Название компании',
        max_length=MAX_LENGTH_COMPANY_NAME,
        blank=True,
        default='',
    )
    address = models.CharField(
        verbose_name='Адрес',
        max_length=MAX_LENGTH_ADDRESS,
        blank=True,
        default='',
    )

    class Meta:
        """Мета-класс для работы с клиентами."""

        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        constraints = (
            models.CheckConstraint(
                name='company_required_for_UL',
                check=Q(entity_type=EntityType.UL, company__gt='')
                | ~Q(entity_type=EntityType.UL),
            ),
        )

    def __str__(self):
        """Возвращает строковое представление клиента.

        Формат:
        - Имя клиента
        - Номер мобильного телефона
        - Наименование компании (если указано)
        """
        base = f'{self.client_name}, тел.{self.mobile_phone}'
        return f'{base}, компания: {self.company}' if self.company else base

    def clean(self):
        """Валидация модели перед сохранением."""
        super().clean()
        validate_company_for_legal(self.company, self.entity_type)

    @property
    def total_duty(self) -> Decimal:
        """Общий баланс по всем заказам клиента.

        Сумма > 0 — клиент должен нам,
        Сумма < 0 — мы должны клиенту (переплата),
        Сумма = 0 — нет долга и переплаты.
        """
        return self.orders.total_duty()


class OrderQuerySet(models.QuerySet):
    """Дополнительные агрегаты для заказов."""

    def total_duty(self) -> Decimal:
        """Общий баланс по выбранным заказам.

        > 0 — клиенты в сумме должны нам,
        < 0 — в сумме переплата.
        """
        qs = self.annotate(services_sum=Sum('services__amount'))
        total = Decimal('0.00')
        for o in qs:
            services_total = o.services_sum or Decimal('0.00')
            total += services_total - o.advance
        return total


class OrderStatus(models.TextChoices):
    """Выбор статуса заказа."""

    IN_WORKING = 'in_working', 'в работе'
    UNDER_APPROVAL = 'under_approval', 'на согласовании'
    WAITING_PART = 'waiting_part', 'ожидает запчасть'
    IN_SERVICE = 'in_service', 'находится в сервисном'
    READY_PICKUP = 'ready_pickup', 'готово к выдаче'
    COMPLETED = 'completed', 'выполнено'
    NOT_RELEVANT = 'not_relevant', 'не актуально'


class Order(models.Model):
    """Модель заказа."""

    number = models.PositiveIntegerField(
        verbose_name='Номер заказа', unique=True, editable=False
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name='Клиент',
        related_name='orders',
    )
    create = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True
    )
    accepted_equipment = models.CharField(
        verbose_name='Принятое оборудование',
        max_length=MAX_LENGTH_COMPONENT_FIELD,
        help_text='Наименование оборудования',
    )
    detail = models.CharField(
        verbose_name='Детали заказа',
        max_length=MAX_LENGTH_COMPONENT_DETAIL,
        help_text='Описание неисправности',
    )
    services = models.ManyToManyField(
        'Service',
        verbose_name='Услуги',
        related_name='orders',
        blank=True,
    )
    advance = models.DecimalField(
        verbose_name='Аванс',
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal('0.00'),
    )
    status = models.CharField(
        verbose_name='Статус заказа',
        choices=OrderStatus.choices,
        default=OrderStatus.IN_WORKING,
        max_length=MAX_LENGTH_ORDER_STATUS,
        db_index=True,
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        """Мета-класс для работы с заказами."""

        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-id',)
        constraints = (
            models.CheckConstraint(
                name='order_accepted_equipment_not_empty',
                check=~Q(accepted_equipment=''),
            ),
            models.CheckConstraint(
                name='order_detail_not_empty',
                check=~Q(detail=''),
            ),
        )

    def __str__(self):
        """Строковое представление номера заказа."""
        return f'Заказ {self.code}'

    def save(self, *args, **kwargs):
        """Сохранение заказа с автоматической генерацией номера."""
        if self._state.adding and not self.number:
            self.number = get_next_value(ORDER_SEQUENCE_NAME)
        return super().save(*args, **kwargs)

    @property
    def code(self) -> str:
        """Генерирует красивый код заказа для отображения."""
        return f'{ORDER_CODE_PREFIX}-{self.number:0{ORDER_CODE_PAD}d}'

    @property
    def total_price(self) -> Decimal:
        """Общая стоимость услуг в заказе."""
        agg = self.services.aggregate(total=Sum('amount'))
        return agg['total'] or Decimal('0.00')

    @property
    def duty(self) -> Decimal:
        """Высчитвает долг клиента, либо переплату."""
        return self.total_price - self.advance


class Category(models.Model):
    """Модель для категорий услуг."""

    title = models.CharField(
        "Наименование", max_length=MAX_LENGTH_OF_NAME_CATEGORY
    )
    slug = models.SlugField("Слаг", unique=True, max_length=MAX_LENGTH_OF_SLUG)

    class Meta:
        """Мета-класс для работы с категориями."""

        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        """Возвращает строковое значение."""
        return self.title


class Service(models.Model):
    """Модель услуг."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name="Категория",
    )
    service_name = models.CharField(
        verbose_name="Наименование услуги",
        max_length=MAX_LENGTH_OF_NAME_SERVICE,
        unique=True,
    )
    amount = models.DecimalField(
        verbose_name='Базовая стоимость',
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal('0.00'),
    )

    class Meta:
        """Мета-класс для работы с услугами."""

        ordering = ('service_name',)
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        """Возвращает строковое значение."""
        return self.service_name


class PurchaseStatus(models.TextChoices):
    """Выбор статуса покупки."""

    AWAITING_RECEIPT = 'awaiting_receipt', 'ожидает получения'
    RECEIVED = 'received', 'получено'
    INSTALLED = 'installed', 'установлено'


class Purchase(models.Model):
    """Модель для закупок запчастей."""

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name='purchases',
        verbose_name='Номер заказа',
        blank=True,
        null=True,
    )
    create = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата создания'
    )
    store = models.CharField(
        verbose_name="Наименование магазина", max_length=MAX_LENGTH_NAME_SHOP
    )
    detail = models.CharField(
        "Детали покупки", max_length=MAX_LENGTH_OF_DETAIL_SHOP
    )
    status = models.CharField(
        choices=PurchaseStatus.choices,
        verbose_name='Статус покупки',
        default=PurchaseStatus.AWAITING_RECEIPT,
        max_length=MAX_LENGTH_PURCHASE_STATUS,
        db_index=True,
    )

    class Meta:
        """Мета-класс для работы с запчастями."""

        ordering = ('-id',)
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
