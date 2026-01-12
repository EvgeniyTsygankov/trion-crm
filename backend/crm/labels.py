"""Словарь меток моделей в родительном падеже для использования в шаблонах."""

from .models import Client, Order, Purchase, Service

GENITIVE_LABELS = {
    Client: 'клиента',
    Order: 'заказа',
    Service: 'услуги',
    Purchase: 'покупки',
}
