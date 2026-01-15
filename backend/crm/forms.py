"""Формы для CRM проекта."""

from django import forms

from .models import (
    Client,
    Order,
    Purchase,
    Service,
)


class ClientForm(forms.ModelForm):
    """Форма для клиекта."""

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
                    'placeholder': 'Введите имя клиента',
                }
            ),
            'mobile_phone': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '+79998887766'}
            ),
            'entity_type': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Название компании (для юр. лиц)',
                }
            ),
            'address': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Домашний адрес (для физ. лиц)',
                }
            ),
        }
        labels = {  # noqa: RUF012
            'client_name': 'Имя клиента',
            'mobile_phone': 'Мобильный телефон',
            'entity_type': 'Тип клиента',
            'company': 'Название компании',
            'address': 'Домашний адрес',
        }
        error_messages = {  # noqa: RUF012
            'mobile_phone': {
                'unique': 'Клиент с таким номером телефона уже существует.',
            },
        }


class OrderForm(forms.ModelForm):
    """Форма для заказа."""

    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Услуги',
    )

    class Meta:
        """Мета-класс для формы Order."""

        model = Order
        fields = (
            'client',
            'accepted_equipment',
            'detail',
            'services',
            'advance',
            'status',
        )
        widgets = {  # noqa: RUF012
            'client': forms.Select(
                attrs={'class': 'form-select js-client-select'}
            ),
            'accepted_equipment': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': ('Наименование устройства, модель, цвет'),
                }
            ),
            'detail': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Описание проблемы или работ...',
                }
            ),
            'advance': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                    'step': 0.01,
                    'placeholder': 'Аванс, ₽',
                }
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


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
    """Форма для заказа."""

    class Meta:
        """Мета-класс для формы Purchase."""

        model = Purchase
        fields = ('order', 'store', 'detail', 'status')
        widgets = {  # noqa: RUF012
            'order': forms.Select(
                attrs={'class': 'form-select', 'placeholder': 'Выберите заказ'}
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
                        'ссылка, номер заказ, дополнительные детали...'
                    ),
                }
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
