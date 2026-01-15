"""Хендлеры, связанные с разделом 'Покупки'.

Содержит обработчики:
- 'Покупки' — вход в раздел и показ подменю фильтров;
- 'Все покупки' — вывод последних покупок без фильтрации по статусу;
- 'Ожидает получения' — покупки со статусом awaiting_receipt;
- 'Получено' — покупки со статусом received;
- 'Установлено' — покупки со статусом installed.

Все варианты используют общий хелпер send_purchases, который проверяет
авторизацию, обращается к API через CRMClient и форматирует вывод.
"""

from .bot import bot, clear_dialog_states, get_crm_or_ask_auth, send_purchases
from .keyboards import purchases_menu_keyboard


@bot.message_handler(func=lambda m: m.text == 'Покупки')
def purchases_menu_command(message):
    """Обрабатывает кнопку 'Покупки'.

    Проверяет авторизацию, сбрасывает состояния других диалогов и
    показывает подменю фильтров покупок (Все / Ожидает / Получено /
    Установлено + 'Меню' и 'Авторизация').
    """
    chat_id = message.chat.id
    crm = get_crm_or_ask_auth(chat_id)
    if not crm:
        return
    clear_dialog_states(chat_id)
    bot.send_message(
        chat_id,
        'Выберите фильтр по покупкам',
        reply_markup=purchases_menu_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == 'Все покупки')
def purchases_all_command(message):
    """Выводит последние покупки без фильтрации по статусу.

    Использует send_purchases(chat_id) с status=None.
    """
    chat_id = message.chat.id
    send_purchases(chat_id)


@bot.message_handler(func=lambda m: m.text == 'Ожидает получения')
def purchases_awaiting_command(message):
    """Выводит покупки со статусом 'ожидает получения'."""
    chat_id = message.chat.id
    send_purchases(chat_id, status='awaiting_receipt')


@bot.message_handler(func=lambda m: m.text == 'Получено')
def purchases_received_command(message):
    """Выводит покупки со статусом 'получено'."""
    chat_id = message.chat.id
    send_purchases(chat_id, status='received')


@bot.message_handler(func=lambda m: m.text == 'Установлено')
def purchases_installed_command(message):
    """Выводит покупки со статусом 'установлено'."""
    chat_id = message.chat.id
    send_purchases(chat_id, status='installed')
