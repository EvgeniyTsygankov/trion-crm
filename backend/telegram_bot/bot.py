"""
Базовая инфраструктура Telegram-бота CRM.

Содержит:
- инициализацию объекта bot;
- глобальные состояния (sessions, login_state, clients_state,
  orders_state);
- общие вспомогательные функции для хендлеров:
  форматирование дат и заказов, проверку доступа по chat_id,
  обращение к CRMClient и вывод основных меню.
"""

from datetime import datetime

import requests
from telebot import TeleBot

from .config import TELEGRAM_ALLOWED_CHAT_IDS, TELEGRAM_BOT_TOKEN
from .constants import (
    MAX_ORDERS_SHOWN,
    MAX_PURCHASES_SHOWN,
    ORDER_STATUS_LABELS,
    PURCHASE_STATUS_LABELS,
)
from .keyboards import main_menu_keyboard
from .logger import logger

bot = TeleBot(token=TELEGRAM_BOT_TOKEN)

# Словари для хранения состояния пользователей
sessions = {}  # Активные сессии пользователей (chat_id -> CRMClient)
login_state = {}  # Состояние процесса авторизации
clients_state = {}  # Состояние поиска клиентов
orders_state = {}  # Состояние поиска заказов


def format_iso_date(date_str: str):
    """Форматирует строку даты из ISO формата в читаемый вид."""
    try:
        iso = date_str.replace('Z', '+00:00')
        dt = datetime.fromisoformat(iso)
        return dt.strftime('%d.%m.%Y')
    except ValueError:
        return date_str


def is_allowed_chat(chat_id: int) -> bool:
    """Проверяет, разрешён ли этому chat_id доступ к боту."""
    if not TELEGRAM_ALLOWED_CHAT_IDS:
        return True
    allowed = chat_id in TELEGRAM_ALLOWED_CHAT_IDS
    if not allowed:
        logger.warning('Неавторизованный chat_id=%s', chat_id)
    return allowed


def get_crm_or_ask_auth(chat_id: int):
    """Вернуть CRMClient или отправить сообщение о необходимой авторизации."""
    crm = sessions.get(chat_id)
    if not crm:
        logger.info(
            'Нет CRM-сессии для chat_id=%s, просим авторизоваться',
            chat_id,
        )
        bot.send_message(
            chat_id, 'Сначала авторизуйтесь через /start и "Авторизация".'
        )
        return None
    return crm


def call_api_or_error(chat_id: int, func, *args, **kwargs):
    """Вызвать метод CRMClient, вернуть результат или None при HTTP-ошибке."""
    try:
        return func(*args, **kwargs)
    except requests.HTTPError:
        logger.exception(
            'HTTPError при вызове %s для chat_id=%s',
            getattr(func, '__name__', repr(func)),
            chat_id,
        )
        bot.send_message(chat_id, 'Ошибка при обращении к API.')
        return None
    except requests.ConnectionError:
        logger.exception(
            'ConnectionError при вызове %s для chat_id=%s',
            getattr(func, '__name__', repr(func)),
            chat_id,
        )
        bot.send_message(chat_id, 'API временно недоступно, попробуйте позже.')
        return None


def show_main_menu(chat_id: int):
    """Показывает главное меню с разделами CRM."""
    bot.send_message(
        chat_id, 'Выберите раздел', reply_markup=main_menu_keyboard()
    )


def send_purchases(chat_id: int, status=None):
    """Отправляет пользователю список покупок (до N записей).

    Работает как общий хелпер для всех фильтров:
      - status=None               → все покупки;
      - status='awaiting_receipt' → только «ожидает получения»;
      - status='received'         → только «получено»;
      - status='installed'        → только «установлено».
    При отсутствии покупок выводит сообщение и возвращает пользователя
    в главное меню.
    """
    crm = get_crm_or_ask_auth(chat_id)
    if not crm:
        return
    purchases = call_api_or_error(chat_id, crm.get_purchases, status=status)
    if purchases is None:
        return
    if not purchases:
        if status is None:
            bot.send_message(chat_id, 'Покупок не найдено')
        else:
            bot.send_message(chat_id, 'Покупок с таким статусом не найдено')
            show_main_menu(chat_id)
        return
    for purchase in purchases[:MAX_PURCHASES_SHOWN]:
        order_code = purchase['order_code'] or '-'
        create_display = format_iso_date(purchase['create'])
        store = purchase['store']
        detail = purchase['detail']
        status_value = purchase['status']
        status_label = PURCHASE_STATUS_LABELS.get(status_value, status_value)
        bot.send_message(
            chat_id,
            (
                f'К заказу: {order_code},\n'
                f'Дата: {create_display},\n'
                f'Магазин: {store},\n'
                f'Детали: {detail},\n'
                f'Статус: {status_label}\n'
            ),
        )


def clear_dialog_states(chat_id: int):
    """Сбрасывает состояния диалогов Клиентов и Заказов для чата."""
    clients_state.pop(chat_id, None)
    orders_state.pop(chat_id, None)


def send_orders_list(chat_id: int, orders: list[dict]):
    """Отправляет список заказов (до N штук) и показывает меню."""
    for order in orders[:MAX_ORDERS_SHOWN]:
        text = format_order_message(order)
        bot.send_message(chat_id, text)
    show_main_menu(chat_id)


def format_order_message(order):
    """Формирует текстовое представление заказа для отправки в чат."""
    code = order['code']
    client_name = order['client_name']
    create_display = format_iso_date(order['create'])
    accepted_equipment = order['accepted_equipment']
    detail = order['detail']
    services = order['services']
    service_names = (
        ', '.join(service['service_name'] for service in services)
        if services
        else '-'
    )
    total_price = order['total_price']
    advance = order['advance']
    duty = order['duty']
    status = order['status']
    status_label = ORDER_STATUS_LABELS.get(status, status)
    return (
        f'Номер заказа: {code},\n'
        f'Клиент: {client_name},\n'
        f'Дата: {create_display},\n'
        f'Принятое оборудование: {accepted_equipment},\n'
        f'Детали заказа: {detail},\n'
        f'Услуги: {service_names},\n'
        f'Стоимость услуг: {total_price},\n'
        f'Аванс: {advance},\n'
        f'Долг клиента: {duty},\n'
        f'Статус: {status_label}\n'
    )
