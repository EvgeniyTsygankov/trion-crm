"""Административная панель Django для управления рецептами и связанными моделями.

Этот модуль регистрирует модели в админ-панели Django и настраивает интерфейс
для удобного управления данными о клиентах, заказах, покупках,
категориях услуг и самих услуг.
"""

from django.contrib import admin

from .forms import ClientForm, OrderForm, PurchaseForm, ServiceForm
from .models import Category, Client, Order, Purchase, Service


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Регистрация модели Client в админ-панели."""

    model = Client
    form = ClientForm
    list_display = (
        'client_name',
        'mobile_phone',
        'entity_type',
        'company',
        'address',
        'total_duty_display',
    )
    search_fields = (
        'client_name',
        'mobile_phone',
    )
    readonly_fields = ('total_duty',)

    @admin.display(description='Общий долг / переплата, ₽')
    def total_duty_display(self, obj):  # noqa: PLR6301
        """Отображение общего баланса по всем заказам клиента."""
        return obj.total_duty


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Регистрация модели Order в админ-панели."""

    model = Order
    form = OrderForm
    list_display = (
        'number',
        'client',
        'create',
        'accepted_equipment',
        'status',
        'total_price_display',
        'advance',
        'duty_display',
    )
    search_fields = ('number', 'client__client_name', 'client__mobile_phone')
    list_filter = ('status', 'create')
    filter_horizontal = ('services',)
    readonly_fields = ('number', 'create', 'code', 'total_price', 'duty')

    @admin.display(description='Сумма услуг, ₽')
    def total_price_display(self, obj):  # noqa: PLR6301
        """Отображение общей стоимости услуг в заказе."""
        return obj.total_price

    @admin.display(description='Баланс по заказу, ₽')
    def duty_display(self, obj):  # noqa: PLR6301
        """Отображение долга / переплаты по заказу."""
        return obj.duty


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Регистрация модели Purchase в админ-панели."""

    model = Purchase
    form = PurchaseForm
    list_display = ('order', 'create', 'store', 'detail', 'status')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Регистрация модели Category в админ-панели."""

    model = Category
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}  # noqa: RUF012


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Регистрация модели Service в админ-панели."""

    model = Service
    form = ServiceForm
    list_display = (
        'category',
        'service_name',
        'amount',
    )
    list_filter = ('category',)
    search_fields = ('service_name',)
