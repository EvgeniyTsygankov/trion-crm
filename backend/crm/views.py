"""Представления для CRM проекта."""

from contextlib import suppress

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Prefetch, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseDetailView,
    BaseListView,
    BaseUpdateView,
)
from .constants import (
    ORDERS_LIMIT_ON_HOMEPAGE,
    SERVICES_LIMIT_ON_PAGE,
)
from .forms import (
    ClientForm,
    OrderForm,
    PurchaseForm,
    ServiceForm,
)
from .models import (
    Category,
    Client,
    EntityType,
    Order,
    OrderStatus,
    Purchase,
    Service,
)


class ClientListView(BaseListView):
    """Представление для отображения списка клиентов.

    Наследует функционал базового ListView с добавлением фильтрации
    и поиска по клиентам. Поддерживает фильтрацию по типу клиента
    (физическое/юридическое лицо) и полнотекстовый поиск.
    """

    model = Client
    template_name = 'crm/clients/list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        """Возвращает отфильтрованный и отсортированный QuerySet клиентов.

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
        """Расширяет контекст шаблона статистикой и данными фильтров.

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
    template_name = 'crm/clients/detail.html'
    context_object_name = 'client'

    def get_queryset(self):
        """Оптимизирует запросы для страницы детального просмотра клиента."""
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    'orders__purchases',
                    queryset=Purchase.objects.order_by('-id'),
                )
            )
        )


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
    template_name = 'crm/clients/delete.html'
    context_object_name = 'client'
    success_url = reverse_lazy('client_list')

    def get_queryset(self):
        """Оптимизирует запросы для страницы подтверждения удаления клиента."""
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    'orders__purchases',
                    queryset=Purchase.objects.order_by('-id'),
                )
            )
        )


class ServiceListView(BaseListView):
    """Список услуг с фильтром по категории и поиском по названию."""

    model = Service
    paginate_by = SERVICES_LIMIT_ON_PAGE
    template_name = 'crm/services/list.html'
    context_object_name = 'services'

    def get_queryset(self):
        """Возвращает QuerySet услуг с фильтрацией по категории и поиску.

        Метод выполняет:
        1. Базовый запрос с оптимизацией (select_related)
        2. Фильтрацию по категории (если указана в параметрах GET)
        3. Поиск по названию услуги (если указан поисковый запрос)
        """
        qs = Service.objects.select_related('category').order_by(
            'service_name'
        )
        category = (self.request.GET.get('category') or '').strip()
        if category:
            qs = qs.filter(category__slug=category)
        search = (self.request.GET.get('search') or '').strip()
        if search:
            qs = qs.filter(Q(service_name__icontains=search))

        return qs

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст шаблона.

        Метод расширяет базовый контекст:
        1. Список всех категорий для фильтрации
        2. Текущие значения фильтров для сохранения состояния формы
        """
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.order_by('title')
        context['current_filters'] = {
            'category': self.request.GET.get('category', ''),
            'search': self.request.GET.get('search', ''),
        }
        return context


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

    def get_success_url(self):  # noqa: PLR6301
        """Перенаправляет на страницу списка услуг."""
        return reverse_lazy('service_list')


class ServiceDeleteView(BaseDeleteView):
    """Класс удаления услуги."""

    model = Service
    template_name = 'crm/services/delete.html'
    context_object_name = 'service'
    success_url = reverse_lazy('service_list')

    def post(self, request, *args, **kwargs):
        """Обрабатывает POST-запрос на удаление услуги."""
        self.object = self.get_object()
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                'Нельзя удалить услугу: она используется в заказах.',
            )
            return redirect('service_list')


class OrderListView(BaseListView):
    """Представление для отображения и фильтрации списка заказов.

    Предоставляет расширенный функционал фильтрации заказов по:
    - статусу заказа
    - типу клиента (физическое/юридическое лицо)
    - диапазону дат создания
    - текстовому поиску по различным полям

    Также включает статистическую информацию по заказам.
    """

    model = Order
    template_name = 'crm/orders/list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        """Возвращает отфильтрованный QuerySet заказов на основе GETпараметров.

        Поддерживает фильтрацию по следующим параметрам:
        - status: статус заказа (из OrderStatus)
        - entity_type: тип клиента (FL/UL)
        - date_from/date_to: диапазон дат создания заказа
        - search: текстовый поиск по полям клиента, оборудования и деталям

        Возвращает:
            QuerySet: Оптимизированный и отфильтрованный список заказов
                     с предзагрузкой связанных данных о клиентах.
        """
        queryset = (
            Order.objects.select_related('client')
            .prefetch_related('service_lines__service')
            .prefetch_related('purchases')
        )
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
            q = (
                Q(client__client_name__icontains=search)
                | Q(client__mobile_phone__icontains=search)
                | Q(accepted_equipment__icontains=search)
                | Q(detail__icontains=search)
            )
            digits = ''.join(ch for ch in search if ch.isdigit())
            if digits:
                q |= Q(number=int(digits))
            queryset = queryset.filter(q)
        return queryset

    def get_context_data(self, **kwargs):
        """Расширяет контекст шаблона статистикой и данными фильтров.

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
    template_name = 'crm/orders/detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Возвращает QuerySet заказов с оптимизацией запросов к БД."""
        return (
            super()
            .get_queryset()
            .select_related('client')
            .prefetch_related('service_lines__service')
        )


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
    template_name = 'crm/orders/delete.html'
    context_object_name = 'order'
    success_url = reverse_lazy('order_list')


class PurchaseListView(BaseListView):
    """Класс списка покупок запчастей."""

    model = Purchase
    template_name = 'crm/purchases/list.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        """Возвращает фильтрованный и отсортированный QuerySet покупок."""
        qs = Purchase.objects.select_related('order__client').order_by('-id')
        store = (self.request.GET.get('store') or '').strip()
        if store:
            qs = qs.filter(store=store)
        search = (self.request.GET.get('search') or '').strip()
        if not search:
            return qs
        q = Q(detail__icontains=search)
        digits = ''.join(ch for ch in search if ch.isdigit())
        if digits:
            with suppress(ValueError):
                q |= Q(order__number=int(digits))
        return qs.filter(q)

    def get_context_data(self, **kwargs):
        """Добавляет дополнительные данные в контекст шаблона.

        Расширяет базовый контекст представления данными для фильтров,
        статистики и текущих параметров запроса.
        """
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        context['stores'] = (
            Purchase.objects.values_list('store', flat=True)
            .distinct()
            .order_by('store')
        )
        context['current_filters'] = {
            'store': self.request.GET.get('store', ''),
            'search': self.request.GET.get('search', ''),
        }
        context['total_purchases'] = qs.count()
        context['physical_amount_purchase'] = qs.filter(
            order__client__entity_type='FL'
        ).count()
        context['legal_amount_purchase'] = qs.filter(
            order__client__entity_type='UL'
        ).count()
        context['without_order_purchase'] = qs.filter(
            order__isnull=True
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
    template_name = 'crm/purchases/detail.html'
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
    template_name = 'crm/purchases/delete.html'
    context_object_name = 'purchase'
    success_url = reverse_lazy('purchase_list')


class HomeView(LoginRequiredMixin, TemplateView):
    """Класс главной страницы CRM системы."""

    template_name = 'crm/home_page.html'

    def get_context_data(self, **kwargs):
        """Формирует контекст данных для главной страницы CRM-системы.

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
        ).order_by('-create')[:ORDERS_LIMIT_ON_HOMEPAGE]
        return context


class AboutView(LoginRequiredMixin, TemplateView):
    """Класс страницы 'О сервисе'."""

    template_name = 'crm/about.html'
