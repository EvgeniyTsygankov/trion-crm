# Telegram‑бот для CRM

Модуль `telegram_bot` — Telegram‑бот, работающий поверх REST API CRM.  
Бот позволяет просматривать информацию о клиентах, заказах и покупках запчастей прямо из Telegram.

Используется библиотека **pyTelegramBotAPI** (`telebot`).

---

## Возможности бота

Функциональность реализована в `handlers_*.py` и `bot.py`.

### Авторизация и доступ

- Команда **`/start`**:
  - проверяет, разрешён ли `chat_id` (`TELEGRAM_ALLOWED_CHAT_IDS`);
  - если пользователь ещё не авторизован в CRM:
    - показывает кнопку **«Авторизация»**;
  - если авторизация уже есть:
    - сразу показывает кнопку **«Меню»**.

- Кнопка **«Авторизация»**:
  - по шагам запрашивает:
    1. логин (`username`);
    2. пароль;
  - затем вызывает `get_tokens(username, password)`:
    - `POST {API_BASE_URL}/api/auth/jwt/create/` (Djoser JWT),
    - ожидает `{"access": "<ACCESS>", "refresh": "<REFRESH>"}`;
  - при успехе:
    - создаётся `CRMClient(access, refresh)` и сохраняется в `sessions[chat_id]`;
    - показывается клавиатура с кнопкой **«Меню»**;
  - при ошибке логин/пароль:
    - сообщение *«Неверный логин или пароль»*;
    - состояние авторизации очищается.

- Ограничение по `chat_id`:
  - если `TELEGRAM_ALLOWED_CHAT_IDS` пустой — бот доступен всем;
  - если задан список ID — только эти chat_id имеют доступ; остальные получают сообщение *«Доступ к этому боту ограничен.»*.

### Главное меню

После успешной авторизации доступна кнопка **«Меню»**, которая открывает главное меню:

- **Клиенты**
- **Заказы**
- **Покупки**

Команда **`/help`** отправляет справочный текст `HELP_TEXT`:

- как запустить бота;
- как авторизоваться;
- что делают разделы «Клиенты», «Заказы», «Покупки»;
- какие фильтры доступны.

---

## Взаимодействие с CRM API

Реализовано в `crm_client.py`.

### Получение токенов

```python
from telegram_bot.crm_client import get_tokens

tokens = get_tokens(username, password)
# делает POST {API_BASE_URL}/api/auth/jwt/create/
# возвращает словарь {'access': '...', 'refresh': '...'}
```

Ожидается, что backend настроен на Djoser JWT (/api/auth/jwt/create/, /api/auth/jwt/refresh/).

## Класс CRMClient

```python
client = CRMClient(access, refresh, base_url=API_BASE_URL)
```
- хранит access_token и refresh_token;
- использует requests.Session с заголовком 'Authorization: Bearer <access>'.

Все HTTP‑запросы идут через _request():

1. делает запрос 'session.request(method, url, **kwargs)';
2. если ответ '401 Unauthorized'
   - вызывает '_refresh()':
      - 'POST /api/auth/jwt/refresh/' с '{"refresh": "<token>"}';
      - при 401 выбрасывает 'RefreshTokenInvalidError';
      - иначе обновляет 'access_token' и заголовок 'Authorization';
   - повторяет запрос ещё раз;
3. при других ошибках 'response.raise_for_status()' выбрасывает 'HTTPError'.

Метод '_extract_results()' позволяет одинаково работать с ответами:
- [{...}, {...}]
- { "results": [ {...}, ... ], "count": ... }

Основные методы:

- 'get_clients(search=None)' → 'GET /api/clients/?search=...'
- 'get_client(client_id)' → 'GET /api/clients/{id}/'
- 'get_orders(status=None, search=None, ordering=None)' → 'GET /api/orders/'
- 'get_order(order_id)' → 'GET /api/orders/{id}/'
- 'get_purchases(status=None, search=None, ordering=None)' → 'GET /api/purchases/'
- 'get_purchase(purchase_id)' → 'GET /api/purchases/{id}/'

В хендлерах все вызовы CRM клиента обёрнуты в функцию call_api_or_error(chat_id, func, ...), которая:

- логирует HTTP/сетевые ошибки;
- отправляет пользователю понятное сообщение:
  - Ошибка при обращении к API.» или
  - «API временно недоступно, попробуйте позже.»

---

## Структура клавиатур

Определена в keyboards.py (ReplyKeyboardMarkup).

- 'start_keyboard(is_authorized)'
  - неавторизован: «Авторизация»;
  - авторизован: «Меню».
- 'menu_only_keyboard()'
  - только «Меню» (после успешной авторизации).
- 'main_menu_keyboard()'
  - Клиенты / Заказы / Покупки.
- 'clients_keyboard()'
  - Меню / Авторизация — внутри раздела «Клиенты».
- 'orders_menu_keyboard()'
  - Поиск / Выбор статуса (рядом),
  - ниже Меню / Авторизация.
- 'orders_search_keyboard()'
  - Меню / Авторизация во время ввода поисковой строки.
- 'orders_status_keyboard()'
  - кнопки статусов заказов (читаемый текст из ORDER_STATUS_TEXT_TO_CODE),
  - ниже Меню / Авторизация.
- 'purchases_menu_keyboard()'
  - Все покупки / Ожидает получения / Получено / Установлено,
  - ниже Меню / Авторизация.

---

## Раздел «Клиенты»

Код: 'handlers_clients.py'.

**Вход в раздел**

- Кнопка «Клиенты»:
  - проверка CRM‑сессии ('get_crm_or_ask_auth');
  - сброс диалоговых состояний ('clear_dialog_states');
  - установка "clients_state[chat_id]['stage'] = 'await_phone'";
  - сообщение:
    > "Введите номер телефона клиента (в формате +7999...)."
  - клавиатура 'clients_keyboard()' (Меню / Авторизация). 

**Поиск по телефону**

- В состоянии 'await_phone':
  - служебные кнопки ('Меню', 'Авторизация', 'Клиенты', 'Заказы', 'Покупки') игнорируются;
  - текст сообщения → номер телефона (например, '+79995556677');
  - через 'crm.get_clients(search=phone)' бот получает список клиентов;
  - если список пуст:
    - сообщение: «Клиенты с таким телефоном не найдены»;
    - показ основного меню;
  - если найден клиент:
    - берётся первый объект;
    - формируется карточка:
      - Имя
      - Телефон
      - Тип (по 'ENTITY_LABELS': 'FL → "физ"', 'UL → "юр"')
      - Компания (или '-', если пусто)
      - Адрес (или '-')
    - сообщение отправляется пользователю;
    - показывается главное меню.
- В 'finally' состояние 'clients_state[chat_id]' очищается.

---

Раздел «Заказы»

Код: 'handlers_orders.py' + общие хелперы в 'bot.py'.

**Вход в раздел**

- Кнопка «Заказы»:
  - проверяет авторизацию;
  - сбрасывает состояния;
  - ставит "orders_state[chat_id]['stage'] = 'orders_menu'";
  - отправляет сообщение:
    > "Выберите действие для заказов:"
  - клавиатура orders_menu_keyboard():
    - верхний ряд: Поиск / Выбор статуса
    - нижний: Меню / Авторизация.

**Поиск заказов по строке**

1. Кнопка «Поиск»:
   -  "stage = 'await_search'";
   -  сообщение‑подсказка:
      -  можно искать по:
         -  номеру телефона клиента ('+7999...');
         -  номеру заказа (например, '101');
         -  наименованию оборудования (например, 'Asus ROG');
      - клавиатура 'orders_search_keyboard()'.
2. В состоянии 'await_search':
    - игнорируются служебные кнопки;
    - текст → 'query';
    - вызывается 'crm.get_orders(search=query)';
    - если список пуст:
      - сообщение: «Заказы по текущей информации отсутствуют»;
      - главное меню;
    - если есть заказы:
      - send_orders_list(chat_id, orders):
        - берёт до 'MAX_ORDERS_SHOWN' заказов;
        - каждый заказ форматируется функцией 'format_order_message(order)' в 'bot.py':
          - Номер заказа (код, например 'TN-00010');
          - Клиент;
          - Дата (через 'format_iso_date');
          - Принятое оборудование;
          - Детали заказа;
          - Список услуг;
          - Стоимость услуг ('total_price');
          - Аванс ('advance');
          - Долг клиента ('duty');
          - Статус (переведён через 'ORDER_STATUS_LABELS' в человекочитаемый вид);
        - после списка снова показывается главное меню.
    - в 'finally' 'orders_state[chat_id]' очищается.

**Фильтр заказов по статусу**

1. Кнопка «Выбор статуса»:
    - "stage = 'await_status'";
    - сообщение: «Выберите статус заказов»;
    - клавиатура 'orders_status_keyboard()':
      - набор кнопок статусов (например, «В работе», «Ожидает запчасть», «Готово к выдаче», ...),
      - плюс Меню / Авторизация.
2. В состоянии 'await_status':  
    - если текст нажатой кнопки есть в 'ORDER_STATUS_TEXT_TO_CODE':
      - текст → код статуса (например, "В работе" → "in_working");
      - из 'sessions[chat_id]' берётся CRM‑клиент;
      - вызывается crm.get_orders(status=status_code);
      - если сессии нет:
        - сообщение: «Сессия авторизации потеряна, залогиньтесь ещё раз.»;
      - если заказов нет:
        - сообщение: «Заказы со статусом "<текст>" отсутствуют»;
        - главное меню;
      - если есть — 'send_orders_list(chat_id, orders)' (как при поиске).
    - в 'finally' 'orders_state[chat_id]' очищается.

---

## Раздел «Покупки»

Код: 'handlers_purchases.py' + 'send_purchases' в 'bot.py'.

**Вход в раздел**

- Кнопка «Покупки»:
  - проверка авторизации;
  - сброс состояний;
  - сообщение:
    > "Выберите фильтр по покупкам"
  - клавиатура 'purchases_menu_keyboard()':
    - Все покупки
    - Ожидает получения
    - Получено
    - Установлено
    - Меню / Авторизация

**Фильтры покупок**

Четыре кнопки:

- «Все покупки» → send_purchases(chat_id, status=None)
- «Ожидает получения» → send_purchases(chat_id, status='awaiting_receipt')
- «Получено» → send_purchases(chat_id, status='received')
- «Установлено» → send_purchases(chat_id, status='installed')

'send_purchases':

- через 'get_crm_or_ask_auth' проверяет авторизацию;
- через 'call_api_or_error(chat_id, crm.get_purchases, status=status)' получает покупки;
- если нет данных:
  - при 'status=None': «Покупок не найдено»;
  - при конкретном статусе: «Покупок с таким статусом не найдено» + главное меню;
- если есть данные:
  - берёт до 'MAX_PURCHASES_SHOWN' покупок;
  - для каждой формирует сообщение:
    - Код заказа ('order_code') или '-';
    - Дата ('create' → 'DD.MM.YYYY');
    - Магазин ('store');
    - Детали ('detail');
    - Статус (по 'PURCHASE_STATUS_LABELS').

---

## Переменные окружения

Читаются в config.py:

```
API_BASE_URL=http://127.0.0.1:8000       # базовый URL API CRM (без завершающего слэша)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...     # токен бота от BotFather

# необязательно; если пусто — бот доступен всем
TELEGRAM_ALLOWED_CHAT_IDS=12345,67890    # список разрешённых chat_id через запятую
```

## Логирование

Настроено в logger.py:

- каталог логов: backend/logs/ (создаётся автоматически);
- основной файл: backend/logs/main.log;
- используется RotatingFileHandler:
  - максимум 50 МБ на файл (maxBytes=50_000_000);
  - до 3 резервных файлов (backupCount=3);
- формат строки лога:
    `YYYY-MM-DD HH:MM:SS - telegram_bot - LEVEL - message`

Логи также дублируются в консоль (StreamHandler).

Через logger пишутся:

- попытки и результаты авторизации;
- HTTP/Connection ошибки при обращении к API CRM;
- проблемы с refresh‑токеном и доступом по chat_id.

---

## Запуск бота

Точка входа: telegram_bot/main.py:

```python
from .bot import bot

def main():
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    main()
```

Запуск из каталога backend: `python -m telegram_bot.main`

Перед запуском убедитесь, что:

1. Настроено и работает backend‑приложение CRM:
   -  запущен Django‑сервер,
   -  доступны эндпоинты '/api/clients/', '/api/orders/', '/api/purchases/',
   -  настроены JWT эндпоинты Djoser: '/api/auth/jwt/create/', '/api/auth/jwt/refresh/'.

2. В '.env' корректно указаны:
   - API_BASE_URL (адрес backend’а),
   - TELEGRAM_BOT_TOKEN,
   - (при необходимости) TELEGRAM_ALLOWED_CHAT_IDS.

После этого бот будет доступен в Telegram и сможет работать с данными вашей CRM.