"""Формы для CRM проекта."""

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .constants import (
    COUNT_SERVICES_IN_ORDER,
    MONEY_DECIMAL_PLACES,
    MONEY_MAX_DIGITS,
    SERVICES_LIMIT_ERROR,
)
from .models import (
    Client,
    Order,
    Purchase,
    Service,
)


class ClientForm(forms.ModelForm):
    """Форма клиента."""

    class Meta:
        """Мета-класс для формы Client."""

        model = Client
        fields = (
            'client_name',
            'mobile_phone',
            'entity_type',
            'company',
            'address',
        )
        widgets = {  # noqa: RUF012
            'client_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'ФИО',
                }
            ),
            'mobile_phone': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '+79998887766'}
            ),
            'entity_type': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'поле для юр. лиц',
                }
            ),
            'address': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'улица, здание, помещение',
                }
            ),
        }
        labels = {  # noqa: RUF012
            'client_name': 'Имя клиента',
            'mobile_phone': 'Мобильный телефон',
            'entity_type': 'Тип клиента',
            'company': 'Название компании',
            'address': 'Адрес',
        }
        error_messages = {  # noqa: RUF012
            'mobile_phone': {
                'unique': 'Клиент с таким номером телефона уже существует.',
            },
        }


class OrderForm(forms.ModelForm):
    """Форма для заказа."""

    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.select_related('category').order_by(
            'category__title', 'service_name'
        ),
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-select js-services-select'}
        ),
        label='Услуги',
    )
    purchases_total = forms.DecimalField(
        label='Товар (покупки), ₽',
        required=False,
        disabled=True,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    total_amount = forms.DecimalField(
        label='Общая сумма, ₽',
        required=False,
        disabled=True,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    duty = forms.DecimalField(
        label='Долг / переплата, ₽',
        required=False,
        disabled=True,
        max_digits=MONEY_MAX_DIGITS,
        decimal_places=MONEY_DECIMAL_PLACES,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        """Мета-класс для формы Order."""

        model = Order
        fields = (
            'client',
            'accepted_equipment',
            'detail',
            'services',
            'services_total_override',
            'purchases_total',
            'total_amount',
            'advance',
            'paid',
            'duty',
            'status',
        )
        widgets = {  # noqa: RUF012
            'client': forms.Select(
                attrs={'class': 'form-select js-client-select'}
            ),
            'accepted_equipment': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Наименование оборудования',
                }
            ),
            'detail': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Описание неисправности',
                    'rows': 4,
                }
            ),
            'services_total_override': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                    'step': 0.01,
                    'placeholder': 'Автоматически заполняется из услуг',
                }
            ),
            'advance': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'step': 0.01}
            ),
            'paid': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'step': 0.01}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        """Инициализация формы заказа.

        - Настраивает отображение услуг в списке (название + цена).
        - При редактировании предзаполняет поле стоимости услуг
        автоматически рассчитанным значением, если override не задан.
        """
        super().__init__(*args, **kwargs)
        self.order_fields(self.Meta.fields)
        self.fields['services'].label_from_instance = (
            lambda s: f'{s.service_name} - {s.amount} ₽'
        )
        self.fields['services'].help_text = SERVICES_LIMIT_ERROR % {
            'limit': COUNT_SERVICES_IN_ORDER
        }
        if (
            self.instance
            and self.instance.pk
            and self.instance.services_total_override is None
        ):
            self.initial['services_total_override'] = (
                self.instance.services_total
            )
        if self.instance and self.instance.pk:
            self.initial['purchases_total'] = self.instance.purchases_total
            self.initial['total_amount'] = self.instance.total_amount
            self.initial['duty'] = self.instance.duty
        else:
            self.initial['purchases_total'] = Decimal('0.00')
            self.initial['total_amount'] = Decimal('0.00')
            self.initial['duty'] = Decimal('0.00')

    def clean_services(self):
        """Валидация поля выбора услуг.

        Проверяет, что выбрано не более COUNT_SERVICES_IN_ORDER услуг.
        Вызывается автоматически при валидации формы.
        """
        services = self.cleaned_data.get('services')
        if services and services.count() > COUNT_SERVICES_IN_ORDER:
            raise ValidationError(
                SERVICES_LIMIT_ERROR,
                code='services_limit',
                params={'limit': COUNT_SERVICES_IN_ORDER},
            )
        return services


class ServiceForm(forms.ModelForm):
    """Форма для услуги."""

    class Meta:
        """Мета-класс для формы Service."""

        model = Service
        fields = ('category', 'service_name', 'amount')
        widgets = {  # noqa: RUF012
            'category': forms.Select(attrs={'class': 'form-select'}),
            'service_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Наименование услуги',
                }
            ),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                    'step': 0.01,
                    'placeholder': 'Базовая стоимость, ₽',
                }
            ),
        }
        error_messages = {  # noqa: RUF012
            'service_name': {
                'unique': 'Услуга с таким наименованием уже существует.',
            },
        }


class PurchaseForm(forms.ModelForm):
    """Форма для покупки."""

    class Meta:
        """Мета-класс для формы Purchase."""

        model = Purchase
        fields = ('order', 'store', 'detail', 'cost', 'status')
        widgets = {  # noqa: RUF012
            'order': forms.Select(
                attrs={'class': 'form-select js-order-select'}
            ),
            'store': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Название магазина',
                }
            ),
            'detail': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': (
                        'Подробное описание покупки: что куплено, цена, '
                        'ссылка, дополнительные детали...'
                    ),
                }
            ),
            'cost': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'step': 0.01}
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        """Настраивает отображение заказов в выпадающем списке."""
        super().__init__(*args, **kwargs)
        self.fields['order'].queryset = Order.objects.select_related(
            'client'
        ).order_by('-id')
        self.fields['order'].label_from_instance = (
            lambda o: f'{o.code} — {o.client.client_name}'
        )
