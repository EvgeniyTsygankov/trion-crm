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


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий услуг."""

    class Meta:
        """Мета-класс для настройки сериализатора Category."""

        model = Category
        fields = ('id', 'title', 'slug')


class PurchaseSerializer(serializers.ModelSerializer):
    """Сериализатор для покупок."""

    order_code = serializers.SerializerMethodField(read_only=True)
    client_name = serializers.SerializerMethodField(read_only=True)
    status = serializers.ChoiceField(choices=PurchaseStatus.choices)

    class Meta:
        """Мета-класс для настройки сериализатора Purchase."""

        model = Purchase
        fields = (
            'id',
            'order_code',
            'create',
            'client_name',
            'store',
            'detail',
            'cost',
            'status',
        )
        read_only_fields = ('create',)

    def get_order_code(self, obj) -> str | None:  # noqa: PLR6301
        """Возвращает код заказа, связанного с покупкой."""
        return obj.order.code if obj.order else None

    def get_client_name(self, obj) -> str | None:  # noqa: PLR6301
        """Возвращает имя клиента или None, если заказ не указан."""
        if not obj.order:
            return None
        return obj.order.client.client_name


class ServiceSerializer(serializers.ModelSerializer):
    """Сериализатор для услуг."""

    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )

    class Meta:
        """Мета-класс для настройки сериализатора Service."""

        model = Service
        fields = (
            'id',
            'category',
            'service_name',
            'amount',
        )


class ServiceInOrderSerializer(serializers.ModelSerializer):
    """Сериализатор услуги в составе заказа."""

    id = serializers.IntegerField(source='service.id', read_only=True)
    service_name = serializers.CharField(
        source='service.service_name', read_only=True
    )

    class Meta:
        """Мета-класс связанных сериализаторов услуг и заказов."""

        model = ServiceInOrder
        fields = ('id', 'service_name', 'amount')


class PurchaseInOrderSerializer(serializers.ModelSerializer):
    """Покупка в составе заказа."""

    status = serializers.ChoiceField(choices=PurchaseStatus.choices)

    class Meta:
        """Мета-класс для настройки сериализатора PurchaseInOrder."""

        model = Purchase
        fields = (
            'id',
            'create',
            'store',
            'detail',
            'cost',
            'status',
        )
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов."""

    client_name = serializers.CharField(
        source='client.client_name',
        read_only=True,
    )
    status = serializers.ChoiceField(choices=OrderStatus.choices)
    mobile_phone = serializers.CharField(
        source='client.mobile_phone', read_only=True
    )
    code = serializers.CharField(read_only=True)
    services = ServiceInOrderSerializer(
        source='service_lines', many=True, read_only=True
    )
    purchases = PurchaseInOrderSerializer(many=True, read_only=True)
    services_total = serializers.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        read_only=True,
    )
    purchases_total = serializers.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        read_only=True,
    )
    total_amount = serializers.DecimalField(
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
    paid = serializers.DecimalField(
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
    )

    class Meta:
        """Мета-класс для настройки сериализатора Order."""

        model = Order
        fields = (
            'id',
            'code',
            'create',
            'client_name',
            'mobile_phone',
            'accepted_equipment',
            'detail',
            'services',
            'purchases',
            'services_total',
            'purchases_total',
            'total_amount',
            'advance',
            'paid',
            'duty',
            'status',
        )
        read_only_fields = (
            'id',
            'code',
            'create',
            'client_name',
            'mobile_phone',
            'services_total',
            'purchases_total',
            'total_amount',
            'duty',
        )
