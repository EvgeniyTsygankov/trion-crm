"""
Хендлеры, связанные с разделом 'Клиенты'.

Содержит обработчики:
- 'Клиенты' — вход в раздел, запрос номера телефона клиента;
- clients_by_phone — поиск и отображение клиента по номеру телефона.

Хендлеры опираются на состояния clients_state и sessions и используют
CRMClient для доступа к API, а также утилиты из telegram_bot.bot
(проверка авторизации, обработка ошибок, форматирование).
"""

from .bot import (
    bot,
    call_api_or_error,
    clear_dialog_states,
    clients_state,
    get_crm_or_ask_auth,
    show_main_menu,
)
from .constants import ENTITY_LABELS
from .keyboards import clients_keyboard


@bot.message_handler(func=lambda m: m.text == 'Клиенты')
def clients_menu_command(message):
    """Обрабатывает кнопку 'Клиенты'.

    Проверяет авторизацию, сбрасывает состояния других диалогов и
    запрашивает номер телефона клиента. Показывает клавиатуру с
    кнопками 'Меню' и 'Авторизация'.
    """
    chat_id = message.chat.id
    crm = get_crm_or_ask_auth(chat_id)
    if not crm:
        return
    clear_dialog_states(chat_id)
    clients_state[chat_id] = {'stage': 'await_phone'}
    bot.send_message(
        chat_id,
        'Введите номер телефона клиента (в формате +7999...).',
        reply_markup=clients_keyboard(),
    )


@bot.message_handler(
    func=lambda m: clients_state.get(m.chat.id, {}).get('stage')
    == 'await_phone'
)
def clients_by_phone(message):
    """Ищет и отображает клиента по номеру телефона."""
    if message.text in {'Меню', 'Авторизация', 'Клиенты', 'Заказы', 'Покупки'}:
        return
    chat_id = message.chat.id
    phone = message.text.strip()
    try:
        crm = get_crm_or_ask_auth(chat_id)
        if not crm:
            return
        clients = call_api_or_error(chat_id, crm.get_clients, search=phone)
        if clients is None:
            return
        if not clients:
            bot.send_message(chat_id, 'Клиенты с таким телефоном не найдены')
            show_main_menu(chat_id)
            return
        client = clients[0]
        name = client['client_name']
        client_phone = client['mobile_phone']
        entity = client['entity_type']
        entity_label = ENTITY_LABELS.get(entity, entity)
        company = client['company']
        address = client['address']
        company_display = '-' if not company else company
        address_display = '-' if not address else address
        bot.send_message(
            chat_id,
            (
                f'Имя: {name},\n'
                f'Телефон: {client_phone},\n'
                f'Тип: {entity_label},\n'
                f'Компания: {company_display},\n'
                f'Адрес: {address_display}\n'
            ),
        )
        show_main_menu(chat_id)
    finally:
        clients_state.pop(chat_id, None)
