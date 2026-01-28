"""Представления для CRM системы.

Этот модуль содержит API endpoints для работы с основными сущностями CRM:
клиентами, заказами и покупками.
"""

from django.db.models import Q
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
                {'detail': 'Параметр ?search= обязателен.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().list(request, *args, **kwargs)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с заказами в режиме только для чтения."""

    queryset = Order.objects.select_related('client').prefetch_related(
        'service_lines__service__category',
        'purchases',
    )
    serializer_class = OrderSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filterset_fields = ('status',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        """Возвращает queryset, опционально применяя поиск по ?search=.

        Поддерживаем:
        - поиск по accepted_equipment (icontains)
        - поиск по телефону клиента (icontains)
        - поиск по номеру заказа (точное совпадение number=int(digits)),
          если в строке поиска удаётся выделить цифры.
        """
        qs = super().get_queryset()
        search = (self.request.query_params.get('search') or '').strip()
        if not search:
            return qs
        q = Q(accepted_equipment__icontains=search) | Q(
            client__mobile_phone__icontains=search
        )
        digits = ''.join(ch for ch in search if ch.isdigit())
        if digits:
            q |= Q(number=int(digits))

        return qs.filter(q)


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

    queryset = Purchase.objects.select_related('order__client')
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
