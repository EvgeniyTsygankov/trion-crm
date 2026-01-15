"""Фабрики клавиатур ReplyKeyboardMarkup для Telegram-бота CRM.

Каждая функция создаёт и возвращает готовую клавиатуру для одного из
режимов работы бота:
- стартовое меню (/start);
- раздел 'Клиенты';
- раздел 'Заказы' (подменю, поиск, выбор статуса);
- раздел 'Покупки' (фильтры по статусу).
"""

from telebot import types

from .constants import ORDER_STATUS_TEXT_TO_CODE


def start_keyboard(is_authorized: bool):
    """Клавиатура для /start: либо 'Авторизация', либо 'Меню'."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_authorized:
        button_menu = types.KeyboardButton('Меню')
        keyboard.add(button_menu)
    else:
        button_auth = types.KeyboardButton('Авторизация')
        keyboard.add(button_auth)
    return keyboard


def menu_only_keyboard():
    """Клавиатура после успешной авторизации: только 'Меню'."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_menu = types.KeyboardButton('Меню')
    keyboard.add(button_menu)
    return keyboard


def main_menu_keyboard():
    """Клавиатура главного меню: Клиенты / Заказы / Покупки."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_clients = types.KeyboardButton('Клиенты')
    button_orders = types.KeyboardButton('Заказы')
    button_purchases = types.KeyboardButton('Покупки')
    keyboard.add(button_clients, button_orders, button_purchases)
    return keyboard


def clients_keyboard():
    """Клавиатура внутри раздела 'Клиенты': Меню / Авторизация."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_menu = types.KeyboardButton('Меню')
    button_auth = types.KeyboardButton('Авторизация')
    keyboard.add(button_menu, button_auth)
    return keyboard


def orders_menu_keyboard():
    """Подменю для раздела 'Заказы': Поиск/Выбор статуса + Меню/Авторизация."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_search = types.KeyboardButton('Поиск')
    button_status = types.KeyboardButton('Выбор статуса')
    button_menu = types.KeyboardButton('Меню')
    button_auth = types.KeyboardButton('Авторизация')
    keyboard.row(button_search, button_status)
    keyboard.row(button_menu, button_auth)
    return keyboard


def orders_search_keyboard():
    """Клавиатура при поиске заказов: Меню / Авторизация."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_menu = types.KeyboardButton('Меню')
    button_auth = types.KeyboardButton('Авторизация')
    keyboard.add(button_menu, button_auth)
    return keyboard


def orders_status_keyboard():
    """Клавиатура выбора статуса заказов + Меню / Авторизация."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton(text) for text in ORDER_STATUS_TEXT_TO_CODE
    ]
    keyboard.row(buttons[0], buttons[1], buttons[2])
    keyboard.row(buttons[3], buttons[4], buttons[5])
    keyboard.row(buttons[6])
    button_menu = types.KeyboardButton('Меню')
    button_auth = types.KeyboardButton('Авторизация')
    keyboard.row(button_menu, button_auth)
    return keyboard


def purchases_menu_keyboard():
    """Подменю раздела 'Покупки': фильтры по статусам + Меню / Авторизация."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_all = types.KeyboardButton('Все покупки')
    button_awaiting = types.KeyboardButton('Ожидает получения')
    button_received = types.KeyboardButton('Получено')
    button_installed = types.KeyboardButton('Установлено')
    button_menu = types.KeyboardButton('Меню')
    button_auth = types.KeyboardButton('Авторизация')
    keyboard.row(button_all, button_awaiting)
    keyboard.row(button_received, button_installed)
    keyboard.row(button_menu, button_auth)
    return keyboard
