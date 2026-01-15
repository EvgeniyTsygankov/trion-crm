"""Представления (ViewSets) для CRM системы.

Этот модуль содержит API endpoints для работы с основными сущностями CRM:
клиентами, заказами и покупками. Используется Django REST Framework
для создания RESTful API с автоматической документацией.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from crm.models import Client, Order, Purchase

from .serializers import ClientSerializer, OrderSerializer, PurchaseSerializer


class ClientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с клиентами в режиме только для чтения.

    Основное использование:
    - GET /api/clients/?search=+7999...  — поиск клиента по телефону
    - GET /api/clients/{id}/             — детальная информация

    Поддерживает поиск клиента по номеру мобильного телефона.
    """

    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('mobile_phone',)

    def list(self, request, *args, **kwargs):
        """Запрещаем /api/clients/ без параметра ?search=."""
        if not request.query_params.get('search'):
            return Response(
                {"detail": "Параметр ?search= обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().list(request, *args, **kwargs)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с заказами в режиме только для чтения.

    Предоставляет следующие API endpoints:
    - GET /api/orders/ - список всех заказов
    - GET /api/orders/{id}/ - детальная информация о заказе

    Особенности:
    - оптимизированные запросы к БД через select_related и prefetch_related;
    - поиск по описанию принятого оборудования и номеру телефона клиента и
    номеру заказа (пример: 101) ;
    - фильтрация по статусу заказа;
    - сортировка по идентификатору заказа (id), по умолчанию — по убыванию.
    """

    queryset = Order.objects.select_related('client').prefetch_related(
        'services', 'services__category'
    )
    serializer_class = OrderSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ('status',)
    search_fields = (
        'accepted_equipment',
        'client__mobile_phone',
        'number',
    )
    ordering_fields = ('id',)
    ordering = ('-id',)


class PurchaseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с покупками (закупками) в режиме только для чтения.

    Предоставляет следующие API endpoints:
    - GET /api/purchases/ - список всех покупок
    - GET /api/purchases/{id}/ - детальная информация о покупке

    Особенности:
    - каждая покупка связана с заказом через ForeignKey (select_related);
    - поддерживается фильтрация по статусу покупки;
    - поддерживается поиск по полю detail (без учёта регистра);
    - сортировка по идентификатору покупки (id), по умолчанию — по убыванию.
    """

    queryset = Purchase.objects.select_related('order')
    serializer_class = PurchaseSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = ('status',)
    search_fields = ('detail',)
    ordering_fields = ('id',)
    ordering = ('-id',)
