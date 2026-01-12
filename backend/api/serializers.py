"""Сериализаторы для проекта CRM."""

from rest_framework import serializers

from crm.models import Category, Client, Order, Purchase, Service


class ClientSerializer(serializers.ModelSerializer):
    """Сериализатор для клиента."""

    class Meta:
        """Мета-класс для сериализатора ClientSerializer."""

        model = Client
        fields = (
            'id',
            'client_name',
            'mobile_phone',
            'entity_type',
            'company',
            'address',
        )


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категории."""

    class Meta:
        """Мета-класс для сериализатора CategorySerializer."""

        model = Category
        fields = (
            'id',
            'title',
            'slug',
        )


class ServiceSerializer(serializers.ModelSerializer):
    """Сериализатор для услуги."""

    category = serializers.SlugRelatedField(read_only=True, slug_field='slug')

    class Meta:
        """Мета-класс для сериализатора ServiceSerializer."""

        model = Service
        fields = (
            'id',
            'category',
            'service_name',
            'amount',
        )


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказа."""

    client = serializers.PrimaryKeyRelatedField(read_only=True)
    client_name = serializers.CharField(
        source='client.client_name', read_only=True
    )
    services = ServiceSerializer(many=True, read_only=True)
    code = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    duty = serializers.ReadOnlyField()

    class Meta:
        """Мета-класс для сериализатора OrderSerializer."""

        model = Order
        fields = (
            'id',
            'code',
            'number',
            'client',
            'client_name',
            'create',
            'accepted_equipment',
            'detail',
            'services',
            'advance',
            'status',
            'total_price',
            'duty',
        )


class PurchaseSerializer(serializers.ModelSerializer):
    """Сериализатор для покупки запчасти."""

    order = serializers.PrimaryKeyRelatedField(read_only=True)
    order_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Мета-класс для сериализатора PurchaseSerializer."""

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

    def get_order_code(self, obj):
        """Возвращает код заказа или None, если заказа нет."""
        if obj.order is None:
            return None
        return obj.order.code
