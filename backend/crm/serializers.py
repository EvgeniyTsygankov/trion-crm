"""Сериализаторы для приложения CRM-системы."""

from rest_framework import serializers

from .constants import MONEY_DECIMAL_PLACES, MONEY_MAX_DIGITS
from .models import (
    Category,
    Client,
    EntityType,
    Order,
    OrderStatus,
    Purchase,
    PurchaseStatus,
    Service,
    ServiceInOrder,
)
from .validators import validate_company_for_legal


class ClientSerializer(serializers.ModelSerializer):
    """Сериализатор для клиентов."""

    entity_type = serializers.ChoiceField(choices=EntityType.choices)

    class Meta:
        """Мета-класс для настройки сериализатора Client."""

        model = Client
        fields = (
            'id',
            'client_name',
            'mobile_phone',
            'entity_type',
            'company',
            'address',
        )

    def validate(self, attrs):
        """Универсальная валидация company/entity_type."""
        entity = attrs.get(
            'entity_type', getattr(self.instance, 'entity_type', None)
        )
        company = attrs.get('company', getattr(self.instance, 'company', ''))
        validate_company_for_legal(company, entity)
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов."""

    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    status = serializers.ChoiceField(choices=OrderStatus.choices)
    mobile_phone = serializers.CharField(
        source='client.mobile_phone', read_only=True
    )
    code = serializers.CharField(read_only=True)
    total_price = serializers.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        read_only=True,
    )
    duty = serializers.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        read_only=True,
    )
    advance = serializers.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )

    class Meta:
        """Мета-класс для настройки сериализатора Order."""

        model = Order
        fields = (
            'id',
            'number',
            'create',
            'code',
            'client',
            'mobile_phone',
            'accepted_equipment',
            'detail',
            'advance',
            'total_price',
            'duty',
            'status',
        )
        read_only_fields = (
            'id',
            'number',
            'create',
            'code',
            'mobile_phone',
            'total_price',
            'duty',
        )


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий услуг."""

    class Meta:
        """Мета-класс для настройки сериализатора Category."""

        model = Category
        fields = ('id', 'title', 'slug')


class PurchaseSerializer(serializers.ModelSerializer):
    """Сериализатор для покупок."""

    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        allow_null=True,
        required=False,
    )
    order_code = serializers.CharField(source='order.code', read_only=True)
    status = serializers.ChoiceField(choices=PurchaseStatus.choices)

    class Meta:
        """Мета-класс для настройки сериализатора Purchase."""

        model = Purchase
        fields = (
            'id',
            'order',
            'order_code',
            'create',
            'store',
            'detail',
            'status',
        )
        read_only_fields = ('create',)


class ServiceSerializer(serializers.ModelSerializer):
    """Сериализатор для услуг."""

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )

    class Meta:
        """Мета-класс для настройки сериализатора Service."""

        model = Service
        fields = ('id', 'category', 'service_name')


class ServiceInOrderSerializer(serializers.ModelSerializer):
    """Сериализатор услуги в составе заказа."""

    service_name = serializers.CharField(
        source='service.service_name', read_only=True
    )
    service_base_amount = serializers.DecimalField(
        source='service.amount',
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        read_only=True,
    )

    class Meta:
        """Мета-класс связанных сериализаторов услуг и заказов."""

        model = ServiceInOrder
        fields = (
            'id',
            'order',
            'service',
            'service_name',
            'service_base_amount',
            'amount',
        )
        read_only_fields = (
            'id',
            'order',
            'service_name',
            'service_base_amount',
        )

    def validate(self, attrs):
        """
        Автоподстановка базовой цены услуги, если сумма не указана.

        Работает при создании и обновлении.
        """
        service = attrs.get('service') or getattr(
            self.instance, 'service', None
        )
        amount = attrs.get('amount', None)
        if service is not None and amount is None:
            attrs['amount'] = service.amount
        return attrs
