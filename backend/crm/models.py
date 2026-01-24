"""Модели для приложения CRM-системы."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
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


class EntityType(models.TextChoices):
    """Выбор вида клиента."""

    FL = 'FL', 'физ'
    UL = 'UL', 'юр'


class Client(models.Model):
    """Модель клиента."""

    client_name = models.CharField(
        verbose_name='Клиент', max_length=MAX_LENGTH_NAME_CLIENT
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
        default=EntityType.FL,
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
                condition=Q(entity_type=EntityType.UL, company__gt='')
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
        """Общий баланс по заказам (услуги + покупки) без раздувания сумм."""
        qs = self.prefetch_related('service_lines', 'purchases')
        total = Decimal('0.00')
        for order in qs:
            services_sum = sum(
                (line.amount or Decimal('0.00'))
                for line in order.service_lines.all()
            )
            purchases_sum = sum(
                (p.cost or Decimal('0.00')) for p in order.purchases.all()
            )
            if order.services_total_override is not None:
                services_total = order.services_total_override
            else:
                services_total = services_sum
            total += (
                services_total + purchases_sum - order.advance - order.paid
            )
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
    )
    detail = models.CharField(
        verbose_name='Описание неисправности',
        max_length=MAX_LENGTH_COMPONENT_DETAIL,
    )
    services = models.ManyToManyField(
        'Service',
        through='ServiceInOrder',
        verbose_name='Услуги',
        related_name='orders',
        blank=True,
    )
    services_total_override = models.DecimalField(
        verbose_name='Услуги, ₽',
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Можно изменить вручную (скидка)',
    )
    advance = models.DecimalField(
        verbose_name='Аванс, ₽',
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    paid = models.DecimalField(
        verbose_name='Оплачено, ₽',
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
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
                condition=~Q(accepted_equipment=''),
            ),
            models.CheckConstraint(
                name='order_detail_not_empty',
                condition=~Q(detail=''),
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
    def services_base_total(self) -> Decimal:
        """Автоматическая сумма услуг по снимкам (история цен)."""
        return self.service_lines.aggregate(total=Sum('amount'))[
            'total'
        ] or Decimal('0.00')

    @property
    def services_total(self) -> Decimal:
        """Стоимость услуг для расчётов/показа: ручная или автоматическая."""
        return (
            self.services_total_override
            if self.services_total_override is not None
            else self.services_base_total
        )

    @property
    def purchases_total(self) -> Decimal:
        """Общая стоимость покупок."""
        agg = self.purchases.aggregate(total=Sum('cost'))
        return agg['total'] or Decimal('0.00')

    @property
    def total_amount(self) -> Decimal:
        """Итого для клиента: услуги (с учётом override) + покупки."""
        return self.services_total + self.purchases_total

    @property
    def duty(self) -> Decimal:
        """Высчитвает долг клиента, либо переплату."""
        return self.total_amount - self.advance - self.paid


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
    """Модель услуги."""

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
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    class Meta:
        """Мета-класс для работы с услугами."""

        ordering = ('service_name',)
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        """Возвращает строковое значение."""
        return self.service_name


class ServiceInOrder(models.Model):
    """Связующая модель 'Услуга в заказе`.

    Реализует связь "многие-ко-многим" между заказами и услугами с
    дополнительными атрибутами. Позволяет хранить индивидуальную стоимость
    услуги для каждого заказа на момемент создания.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='service_lines',
        verbose_name='Заказ',
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='order_lines',
        verbose_name='Услуга',
    )
    amount = models.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        verbose_name='Стоимость услуги в заказе',
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True,
        blank=True,
    )

    class Meta:
        """Метаданные модели ServiceInOrder."""

        verbose_name = 'Услуга в заказе'
        verbose_name_plural = 'Услуги в заказах'
        ordering = ('order', 'service')
        constraints = (
            models.UniqueConstraint(
                fields=('order', 'service'),
                name='uniq_service_per_order',
            ),
        )

    def __str__(self) -> str:
        """Строковое представление записи."""
        return (
            f'{self.order.code}: {self.service.service_name} = {self.amount}'
        )

    def save(self, *args, **kwargs):
        """Устанавливает стоимость из услуги, если amount не указан.

        Фиксирует стоимость услуги на момент создания заказа,
        обеспечивая сохранение исторических данных о ценах.
        """
        if self.amount is None and self.service_id:
            self.amount = self.service.amount
        return super().save(*args, **kwargs)


@receiver(m2m_changed, sender=ServiceInOrder)
def snapshot_service_amount(
    sender, instance, action, pk_set, reverse, **kwargs
):
    """После добавления услуг в заказ — зафиксировать цену в ServiceInOrder."""
    if reverse:
        return
    if action != 'post_add' or not pk_set:
        return
    lines = ServiceInOrder.objects.filter(
        order=instance,
        service_id__in=pk_set,
        amount__isnull=True,
    ).select_related('service')
    for line in lines:
        line.amount = line.service.amount
    if lines:
        ServiceInOrder.objects.bulk_update(lines, ['amount'])


class PurchaseStatus(models.TextChoices):
    """Выбор статуса покупки."""

    DELIVERY_EXPECTED = 'delivery_expected', 'ожидается поставка'
    RECEIVED = 'received', 'получено'
    INSTALLED = 'installed', 'установлено'


class Purchase(models.Model):
    """Модель покупки (запчасть/ПО)."""

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
        verbose_name='Наименование магазина', max_length=MAX_LENGTH_NAME_SHOP
    )
    detail = models.CharField(
        'Детали покупки', max_length=MAX_LENGTH_OF_DETAIL_SHOP
    )
    cost = models.DecimalField(
        verbose_name='Стоимость покупки',
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    status = models.CharField(
        choices=PurchaseStatus.choices,
        verbose_name='Статус покупки',
        default=PurchaseStatus.DELIVERY_EXPECTED,
        max_length=MAX_LENGTH_PURCHASE_STATUS,
        db_index=True,
    )

    class Meta:
        """Мета-класс для работы с запчастями."""

        ordering = ('-id',)
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'

    def __str__(self):
        """Возвращает строковое представление покупки."""
        order_code = self.order.code if self.order else 'без заказа'
        return f'Покупка для заказа {order_code}, {self.detail}, {self.store}'
