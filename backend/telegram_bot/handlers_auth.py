"""Хендлеры авторизации и верхнеуровневого управления ботом.

Содержит обработчики:
- /start — запуск бота, показ 'Авторизация' или 'Меню';
- 'Авторизация' — начало ввода логина и пароля;
- auth_command — поэтапный ввод логина и пароля;
- 'Меню' — показ главного меню;
- /help — вывод справочной информации.

Хендлеры используют общий объект bot и состояния sessions, login_state,
а также вспомогательные функции из telegram_bot.bot.
"""

import requests

from .bot import (
    bot,
    clear_dialog_states,
    get_crm_or_ask_auth,
    is_allowed_chat,
    login_state,
    sessions,
    show_main_menu,
)
from .constants import HELP_TEXT
from .crm_client import CRMClient, get_tokens
from .keyboards import menu_only_keyboard, start_keyboard
from .logger import logger


@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start - инициализирует сессию пользователя.

    Для неавторизованных показывает кнопку 'Авторизация'.
    Для авторизованных — кнопку 'Меню' и сообщение 'Выберите раздел'
    """
    chat_id = message.chat.id
    if not is_allowed_chat(chat_id):
        bot.send_message(chat_id, 'Доступ к этому боту ограничен.')
        return
    is_authorized = chat_id in sessions
    if not is_authorized:
        text = (
            'Добро пожаловать в информационный центр CRM системы.\n'
            'Пожалуйста авторизуйтесь.'
        )
    else:
        text = 'Выберите раздел меню.'
    bot.send_message(
        chat_id,
        text,
        reply_markup=start_keyboard(is_authorized),
    )


@bot.message_handler(func=lambda m: m.text == 'Авторизация')
def login_auth(message):
    """Начинает процесс авторизации - запрашивает логин."""
    chat_id = message.chat.id
    login_state[chat_id] = {'stage': 'await_username'}
    bot.send_message(chat_id, 'Введите логин')


@bot.message_handler(
    func=lambda m: login_state.get(m.chat.id, {}).get('stage') is not None,
    content_types=['text'],
)
def auth_command(message):
    """Обрабатывает поэтапный ввод логина и пароля."""
    chat_id = message.chat.id
    state = login_state.get(chat_id, {}).get('stage')
    if message.text in {'Авторизация', 'Меню', 'Клиенты', 'Заказы', 'Покупки'}:
        return
    if state == 'await_username':
        username = message.text.strip()
        login_state[chat_id]['username'] = username
        login_state[chat_id]['stage'] = 'await_password'
        bot.send_message(chat_id, 'Введите пароль')
        return
    if state == 'await_password':
        username = login_state[chat_id]['username']
        password = message.text
        try:
            tokens = get_tokens(username, password)
        except requests.HTTPError:
            logger.warning(
                'Неуспешная авторизация: username=%s, chat_id=%s',
                username,
                chat_id,
            )
            bot.send_message(chat_id, 'Неверный логин или пароль')
            login_state.pop(chat_id, None)
            return
        access = tokens['access']
        refresh = tokens['refresh']
        client = CRMClient(access, refresh)
        sessions[chat_id] = client
        login_state.pop(chat_id, None)
        logger.info(
            'Успешная авторизация: username=%s, chat_id=%s',
            username,
            chat_id,
        )
        bot.send_message(
            chat_id,
            (
                'Авторизация успешна! Выберите раздел меню.\n'
                'Справочная информация в разделе /help.'
            ),
            reply_markup=menu_only_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text == 'Меню')
def menu_command(message):
    """Обрабатывает кнопку 'Меню': показывает главное меню.

    При отсутствии активной сессии предлагает пройти авторизацию.
    """
    chat_id = message.chat.id
    crm = get_crm_or_ask_auth(chat_id)
    if not crm:
        return
    clear_dialog_states(chat_id)
    show_main_menu(chat_id)


@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработчик команды /help - отправляет справочную информацию."""
    chat_id = message.chat.id
    bot.send_message(chat_id, HELP_TEXT)
