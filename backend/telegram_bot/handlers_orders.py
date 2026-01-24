"""Хендлеры, связанные с разделом 'Заказы'.

Содержит обработчики:
- 'Заказы' — вход в раздел и показ подменю (Поиск / Выбор статуса);
- orders_search_start — переход к вводу строки поиска;
- orders_by_search — поиск заказов по телефону, номеру заказа или
  наименованию оборудования;
- orders_status_menu — показ клавиатуры со статусами заказов;
- orders_by_status — фильтрация и вывод заказов по выбранному статусу.

Хендлеры используют состояние orders_state, CRMClient для работы с API
и общие утилиты из telegram_bot.bot (format_order_message,
send_orders_list, обработку ошибок и т.п.).
"""

from .bot import (
    bot,
    call_api_or_error,
    clear_dialog_states,
    get_crm_or_ask_auth,
    orders_state,
    send_orders_list,
    sessions,
    show_main_menu,
)
from .constants import ORDER_STATUS_TEXT_TO_CODE, SERVICE_BUTTONS
from .keyboards import (
    orders_menu_keyboard,
    orders_search_keyboard,
    orders_status_keyboard,
)


@bot.message_handler(func=lambda m: m.text == 'Заказы')
def orders_menu_command(message):
    """Обрабатывает кнопку 'Заказы'.

    Проверяет авторизацию, сбрасывает состояния других диалогов и
    показывает подменю для заказов: 'Поиск' / 'Выбор статуса' плюс
    кнопки 'Меню' и 'Авторизация'.
    """
    chat_id = message.chat.id
    crm = get_crm_or_ask_auth(chat_id)
    if not crm:
        return
    clear_dialog_states(chat_id)
    orders_state[chat_id] = {'stage': 'orders_menu'}
    bot.send_message(
        chat_id,
        'Выберите действие для заказов:',
        reply_markup=orders_menu_keyboard(),
    )


@bot.message_handler(
    func=lambda m: orders_state.get(m.chat.id, {}).get('stage')
    == 'orders_menu'
    and m.text == 'Поиск'
)
def orders_search_start(message):
    """Переводит раздел 'Заказы' в режим текстового поиска.

    Устанавливает stage='await_search' и отправляет подсказку о том,
    что можно искать по телефону, номеру заказа или оборудованию.
    """
    chat_id = message.chat.id
    orders_state[chat_id]['stage'] = 'await_search'
    bot.send_message(
        chat_id,
        (
            'Поиск по номеру телефона клиента (в формате +7999...) /\n'
            'номеру заказа (пример: TN-00001) /\n'
            'наименованию оборудования (пример: Asus ROG)'
        ),
        reply_markup=orders_search_keyboard(),
    )


@bot.message_handler(
    func=lambda m: (
        orders_state.get(m.chat.id, {}).get('stage') == 'await_search'
        and (m.text not in SERVICE_BUTTONS)
    )
)
def orders_by_search(message):
    """Ищет и отображает заказы по введённой строке.

    По следующим критериям:
    - номер телефона клиента;
    - номер заказа;
    - наименование оборудования.
    При отсутствии результатов выводит сообщение и возвращает в меню.
    """
    chat_id = message.chat.id
    query = message.text.strip()
    try:
        crm = get_crm_or_ask_auth(chat_id)
        if not crm:
            return
        orders = call_api_or_error(chat_id, crm.get_orders, search=query)
        if orders is None:
            return
        if not orders:
            bot.send_message(
                chat_id, 'Заказы по текущей информации отсутствуют'
            )
            show_main_menu(chat_id)
            return
        send_orders_list(chat_id, orders)
    finally:
        orders_state.pop(chat_id, None)


@bot.message_handler(
    func=lambda m: orders_state.get(m.chat.id, {}).get('stage')
    == 'orders_menu'
    and m.text == 'Выбор статуса'
)
def orders_status_menu(message):
    """Показывает подменю выбора статуса заказов.

    Переводит stage в 'await_status' и отображает кнопки со статусами
    в человекочитаемом виде, а также 'Меню' и 'Авторизация'.
    """
    chat_id = message.chat.id
    orders_state[chat_id]['stage'] = 'await_status'
    bot.send_message(
        chat_id,
        'Выберите статус заказов',
        reply_markup=orders_status_keyboard(),
    )


@bot.message_handler(
    func=lambda m: (
        orders_state.get(m.chat.id, {}).get('stage') == 'await_status'
        and m.text in ORDER_STATUS_TEXT_TO_CODE
    )
)
def orders_by_status(message):
    """Показывает список заказов с выбранным статусом.

    Преобразует текст кнопки статуса в код через
    ORDER_STATUS_TEXT_TO_CODE, вызывает crm.get_orders(status=...),
    выводит найденные заказы через send_orders_list либо сообщает,
    что заказов с таким статусом нет.
    """
    chat_id = message.chat.id
    status_code = ORDER_STATUS_TEXT_TO_CODE[message.text]

    try:
        crm = sessions.get(chat_id)
        if not crm:
            bot.send_message(
                chat_id, 'Сессия авторизации потеряна, залогиньтесь ещё раз.'
            )
            return
        orders = call_api_or_error(chat_id, crm.get_orders, status=status_code)
        if orders is None:
            return
        if not orders:
            bot.send_message(
                chat_id, f'Заказы со статусом "{message.text}" отсутствуют'
            )
            show_main_menu(chat_id)
            return
        send_orders_list(chat_id, orders)
    finally:
        orders_state.pop(chat_id, None)
