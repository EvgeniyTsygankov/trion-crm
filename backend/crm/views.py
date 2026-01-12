"""Представления для CRM проекта."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseDetailView,
    BaseListView,
    BaseUpdateView,
)
from .constants import RECENT_ORDERS_LIMIT
from .forms import (
    ClientForm,
    OrderForm,
    PurchaseForm,
    ServiceForm,
)
from .models import (
    Client,
    EntityType,
    Order,
    OrderStatus,
    Purchase,
    Service,
)


class ClientListView(BaseListView):
    """
    Представление для отображения списка клиентов.

    Наследует функционал базового ListView с добавлением фильтрации
    и поиска по клиентам. Поддерживает фильтрацию по типу клиента
    (физическое/юридическое лицо) и полнотекстовый поиск.
    """

    model = Client
    template_name = 'crm/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        """
        Возвращает отфильтрованный и отсортированный QuerySet клиентов.

        Обрабатывает GET-параметры для фильтрации:
        - entity_type: фильтр по типу клиента (FL/UL)
        - search: поиск по имени, телефону, компании или адресу
        """
        qs = Client.objects.all().order_by("-id")

        entity_type = self.request.GET.get("entity_type")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        search = (self.request.GET.get("search") or "").strip()
        if search:
            q = (
                Q(client_name__icontains=search)
                | Q(mobile_phone__icontains=search)
                | Q(company__icontains=search)
                | Q(address__icontains=search)
            )
            digits = "".join(ch for ch in search if ch.isdigit())
            if digits and digits != search:
                q |= Q(mobile_phone__icontains=digits) | Q(
                    mobile_phone__icontains="+" + digits
                )
            qs = qs.filter(q)
        return qs

    def get_context_data(self, **kwargs):
        """
        Расширяет контекст шаблона статистикой и данными фильтров.

        Добавляет в контекст:
        - Статистику клиентов: общее количество, количество физ. и юр. лиц
        - Список вариантов типов клиентов для выпадающего меню фильтра
        - Текущие значения фильтров для сохранения состояния формы

        Статистика вычисляется одним агрегирующим запросом для оптимизации.
        """
        context = super().get_context_data(**kwargs)
        stats = Client.objects.aggregate(
            total_clients=Count('id'),
            physical_count=Count('id', filter=Q(entity_type=EntityType.FL)),
            legal_count=Count('id', filter=Q(entity_type=EntityType.UL)),
        )
        context.update(stats)
        context['entity_type_choices'] = EntityType.choices
        context['current_filters'] = {
            'entity_type': self.request.GET.get('entity_type', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


class ClientCreateView(BaseCreateView):
    """Класс создания клиента."""

    model = Client
    form_class = ClientForm
    success_url = reverse_lazy('client_list')
    success_message = 'Клиент успешно создан!'


class ClientDetailView(BaseDetailView):
    """Класс просмотра клиента."""

    model = Client
    template_name = 'crm/client_detail.html'
    context_object_name = 'client'


class ClientUpdateView(BaseUpdateView):
    """Класс редактирования клиента."""

    model = Client
    form_class = ClientForm
    success_message = 'Данные клиента успешно обновлены!'

    def get_success_url(self):
        """Перенаправляет на страницу обновленного клиента."""
        return reverse_lazy('client_detail', kwargs={'pk': self.object.pk})


class ClientDeleteView(BaseDeleteView):
    """Класс удаления клиента."""

    model = Client
    template_name = 'crm/client_confirm_delete.html'
    context_object_name = 'client'
    success_url = reverse_lazy('client_list')


class ServiceListView(BaseListView):
    """Класс списка услуг."""

    model = Service
    template_name = 'crm/service_list.html'
    context_object_name = 'services'


class ServiceCreateView(BaseCreateView):
    """Класс создания услуги."""

    model = Service
    form_class = ServiceForm
    success_url = reverse_lazy('service_list')
    success_message = 'Услуга создана!'


class ServiceUpdateView(BaseUpdateView):
    """Класс редактирования услуги."""

    model = Service
    form_class = ServiceForm
    success_message = 'Услуга обновлена!'

    def get_success_url(self):
        """Перенаправляет на страницу списка услуг."""
        return reverse_lazy('service_list')


class ServiceDeleteView(BaseDeleteView):
    """Класс удаления услуги."""

    model = Service
    http_method_names = ('post',)
    success_url = reverse_lazy('service_list')


class OrderListView(BaseListView):
    """
    Представление для отображения и фильтрации списка заказов.

    Предоставляет расширенный функционал фильтрации заказов по:
    - статусу заказа
    - типу клиента (физическое/юридическое лицо)
    - диапазону дат создания
    - текстовому поиску по различным полям

    Также включает статистическую информацию по заказам.
    """

    model = Order
    template_name = 'crm/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        """
        Возвращает отфильтрованный QuerySet заказов на основе GET-параметров.

        Поддерживает фильтрацию по следующим параметрам:
        - status: статус заказа (из OrderStatus)
        - entity_type: тип клиента (FL/UL)
        - date_from/date_to: диапазон дат создания заказа
        - search: текстовый поиск по полям клиента, оборудования и деталям

        Возвращает:
            QuerySet: Оптимизированный и отфильтрованный список заказов
                     с предзагрузкой связанных данных о клиентах.
        """
        queryset = Order.objects.select_related('client')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        entity_type = self.request.GET.get('entity_type')
        if entity_type:
            queryset = queryset.filter(client__entity_type=entity_type)
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(create__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(create__date__lte=date_to)
        search = (self.request.GET.get('search') or '').strip()
        if search:
            queryset = (
                Q(client__client_name__icontains=search)
                | Q(client__mobile_phone__icontains=search)
                | Q(accepted_equipment__icontains=search)
                | Q(detail__icontains=search)
            )
            digits = ''.join(ch for ch in search if ch.isdigit())
            if digits:
                queryset |= Q(number=int(digits))
            queryset = queryset.filter(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        """
        Расширяет контекст шаблона статистикой и данными фильтров.

        Добавляет в контекст:
        - Общую статистику по заказам
        - Количественные показатели по типам клиентов
        - Общий баланс (долг) по всем заказам
        - Данные для фильтров (списки выбора)
        - Текущие значения фильтров
        - Статистику по статусам заказов
        """
        context = super().get_context_data(**kwargs)
        context['total_orders'] = Order.objects.count()
        context['physical_amount_order'] = Order.objects.filter(
            client__entity_type='FL'
        ).count()
        context['legal_amount_order'] = Order.objects.filter(
            client__entity_type='UL'
        ).count()
        context['total_duty'] = Order.objects.total_duty()
        context['status_choices'] = OrderStatus.choices
        context['entity_type_choices'] = EntityType.choices
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'entity_type': self.request.GET.get('entity_type', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'search': self.request.GET.get('search', ''),
        }
        context['status_stats'] = {
            status[0]: Order.objects.filter(status=status[0]).count()
            for status in OrderStatus.choices
        }
        return context


class OrderCreateView(BaseCreateView):
    """Класс создания заказа."""

    model = Order
    form_class = OrderForm
    success_url = reverse_lazy('order_list')
    success_message = 'Заказ успешно создан!'


class OrderDetailView(BaseDetailView):
    """Класс просмотра заказа."""

    model = Order
    template_name = 'crm/order_detail.html'
    context_object_name = 'order'


class OrderUpdateView(BaseUpdateView):
    """Класс редактирования заказа."""

    model = Order
    form_class = OrderForm
    success_message = 'Данные заказа успешно обновлены!'

    def get_success_url(self):
        """После сохранения возвращаемся на просмотр заказа."""
        return reverse_lazy('order_detail', kwargs={'pk': self.object.pk})


class OrderDeleteView(BaseDeleteView):
    """Класс удаления заказа."""

    model = Order
    template_name = 'crm/order_confirm_delete.html'
    context_object_name = 'order'
    success_url = reverse_lazy('order_list')


class PurchaseListView(BaseListView):
    """Класс списка покупок запчастей."""

    model = Purchase
    template_name = 'crm/purchase_list.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        """Возвращает оптимизированный QuerySet покупок."""
        return Purchase.objects.select_related('order__client')

    def get_context_data(self, **kwargs):
        """Добавляет статистику по покупкам в контекст шаблона."""
        context = super().get_context_data(**kwargs)
        qs = Purchase.objects.select_related('order__client')
        context['total_purchases'] = qs.count()
        context['physical_amount_purchase'] = qs.filter(
            order__client__entity_type='FL'
        ).count()
        context['legal_amount_purchase'] = qs.filter(
            order__client__entity_type='UL'
        ).count()
        return context


class PurchaseCreateView(BaseCreateView):
    """Класс создания покупки запчасти."""

    model = Purchase
    form_class = PurchaseForm
    success_url = reverse_lazy('purchase_list')
    success_message = 'Покупка запчасти успешно создана!'


class PurchaseDetailView(BaseDetailView):
    """Класс просмотра покупки запчасти."""

    model = Purchase
    template_name = 'crm/purchase_detail.html'
    context_object_name = 'purchase'


class PurchaseUpdateView(BaseUpdateView):
    """Класс редактирования покупки запчасти."""

    model = Purchase
    form_class = PurchaseForm
    success_message = 'Данные покупки успешно обновлены!'

    def get_success_url(self):
        """После сохранения возвращаемся на просмотр покупки запчасти."""
        return reverse_lazy('purchase_detail', kwargs={'pk': self.object.pk})


class PurchaseDeleteView(BaseDeleteView):
    """Класс удаления покупки запчасти."""

    model = Purchase
    template_name = 'crm/purchase_confirm_delete.html'
    context_object_name = 'purchase'
    success_url = reverse_lazy('purchase_list')


class HomeView(LoginRequiredMixin, TemplateView):
    """Главная страница CRM."""

    template_name = 'crm/home_page.html'

    def get_context_data(self, **kwargs):
        """
        Формирует контекст данных для главной страницы CRM-системы.

        Собирает ключевые бизнес-метрики и аналитику по заказам:
        - Общие счетчики заказов и клиентов
        - Количество активных заказов
        - Финансовые показатели (услуги, авансы, задолженность)
        - Список последних заказов для мониторинга активности
        """
        context = super().get_context_data(**kwargs)
        context['total_orders'] = Order.objects.count()
        context['total_clients'] = Client.objects.count()
        context['active_orders_count'] = Order.objects.exclude(
            status__in=[OrderStatus.COMPLETED, OrderStatus.NOT_RELEVANT]
        ).count()
        context['total_duty'] = Order.objects.total_duty()
        context['recent_orders'] = Order.objects.select_related(
            'client'
        ).order_by('-create')[:RECENT_ORDERS_LIMIT]
        return context
