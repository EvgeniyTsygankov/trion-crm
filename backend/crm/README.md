# Приложение `crm` (веб‑интерфейс CRM)

Приложение `crm` — основное Django‑приложение, реализующее веб‑интерфейс CRM‑системы для сервисного центра по ремонту техники.

Здесь находятся:

- доменные модели (клиенты, заказы, услуги, покупки);
- представления (ListView / DetailView / CRUD) и формы;
- HTML‑шаблоны (Django templates);
- административная панель Django.

> Весь интерфейс приложения `crm` доступен **только авторизованным пользователям** (`LoginRequiredMixin`).

---

## Структура приложения

Основные модули:

- [`models.py`](models.py) — модели `Client`, `Order`, `Service`, `Category`, `Purchase` и перечисления статусов.
- [`views.py`](views.py) — представления для клиентов, заказов, услуг, покупок и главной страницы.
- [`urls.py`](urls.py) — маршруты веб‑интерфейса (`/clients/`, `/orders/`, `/purchases/`, `/services/`, `/`).
- [`forms.py`](forms.py) — `ModelForm` для клиентов, заказов, услуг и покупок.
- [`base_views.py`](base_views.py) — общие базовые классы (List/Create/Update/Detail/Delete).
- [`mixins.py`](mixins.py), [`labels.py`](labels.py) — миксин для автоматических заголовков форм.
- [`validators.py`](validators.py) — валидация телефона и бизнес‑правило для юр. лиц.
- [`constants.py`](constants.py) — константы (длины полей, деньги, пагинация, лимит последних заказов).
- [`admin.py`](admin.py) — настройки административной панели Django.

---

## Маршруты и разделы интерфейса

Маршруты определены в [`urls.py`](urls.py).

### Главная страница (дашборд)

- `GET /` → `HomeView` (`TemplateView`, `crm/home_page.html`).

Контекст:

- `total_orders` — общее количество заказов.
- `total_clients` — общее количество клиентов.
- `active_orders_count` — количество **активных** заказов  
  (все, кроме `completed` и `not_relevant`).
- `total_duty` — суммарный баланс по всем заказам (`Order.objects.total_duty()`).
- `recent_orders` — список последних заказов (лимит `RECENT_ORDERS_LIMIT`), с предзагруженными клиентами.

### Клиенты

Маршруты:

- `GET /clients/` → `ClientListView`
- `GET /clients/create/` → `ClientCreateView`
- `GET /clients/<id>/` → `ClientDetailView`
- `GET /clients/<id>/edit/` → `ClientUpdateView`
- `GET /clients/<id>/delete/` → `ClientDeleteView`

#### Список клиентов (`ClientListView`, `crm/client_list.html`)

Функциональность:

- Пагинация через `BaseListView` (`QUANTITY_ON_PAGE` элементов на страницу).
- Сортировка по убыванию `id` (новые клиенты сверху).
- Фильтрация по типу клиента:
  - GET‑параметр `entity_type` (`FL` — физ., `UL` — юр.).
- Поиск (GET‑параметр `search`):
  - по имени (`client_name`),
  - по телефону (`mobile_phone`) — включая ввод только цифр,
  - по компании (`company`),
  - по адресу (`address`).

Статистика (агрегируется одним запросом в `get_context_data()`):

- `total_clients` — общее количество клиентов.
- `physical_count` — количество клиентов с `entity_type=FL`.
- `legal_count` — количество клиентов с `entity_type=UL`.

Дополнительный контекст:

- `entity_type_choices` — варианты типов клиента для `<select>`.
- `current_filters` — текущие значения фильтров (для сохранения состояния формы).

В таблице отображаются:

- имя;
- мобильный телефон;
- тип (бейдж “физ” / “юр”);
- компания;
- адрес;
- количество заказов клиента (`client.orders_count` или аналогичная аннотация);
- суммарный долг/переплата (`client.total_duty`);
- кнопки действий (просмотр / редактирование / удаление).

#### Создание / редактирование / удаление

- `ClientCreateView` / `ClientUpdateView` используют `ClientForm` и общий шаблон `crm/create.html`.
- После создания — редирект на `/clients/`.
- После редактирования — редирект на страницу просмотра клиента (`/clients/<id>/`).
- `ClientDeleteView` использует шаблон `crm/client_confirm_delete.html` и после удаления редиректит на `/clients/`.

Форма `ClientForm`:

- валидирует телефон по маске `+7XXXXXXXXXX`;
- проверяет уникальность телефона (с пользовательским сообщением);
- валидация “у юр. лиц `company` обязательна” реализована на уровне модели и сериализатора, так что правило едино и для веба, и для API.

---

### Заказы

Маршруты:

- `GET /orders/` → `OrderListView`
- `GET /orders/create/` → `OrderCreateView`
- `GET /orders/<id>/` → `OrderDetailView`
- `GET /orders/<id>/edit/` → `OrderUpdateView`
- `GET /orders/<id>/delete/` → `OrderDeleteView`

#### Список заказов (`OrderListView`, `crm/order_list.html`)

Запрос:

- базовый QuerySet: `Order.objects.select_related('client')`.

Фильтры:

- `status` — фильтрация по статусу (`OrderStatus`, поле `Order.status`).
- `entity_type` — тип клиента (`Client.entity_type`).
- `date_from`, `date_to` — фильтрация по дате создания (`create__date__gte/lte`).
- `search` — текстовый поиск:
  - по имени клиента,
  - по телефону клиента,
  - по принятому оборудованию,
  - по деталям заказа,
  - по номеру заказа (`number`, если из поисковой строки удаётся выделить цифры).

Статистика (в `get_context_data()`):

- `total_orders` — общее количество заказов.
- `physical_amount_order` — количество заказов клиентов‑физлиц.
- `legal_amount_order` — количество заказов клиентов‑юрлиц.
- `total_duty` — суммарный баланс по всем заказам (`Order.objects.total_duty()`).
- `status_choices` — список статусов заказа для фильтра.
- `entity_type_choices` — типы клиентов для фильтра.
- `current_filters` — текущие значения всех фильтров (status, entity_type, date_from, date_to, search).
- `status_stats` — словарь `{статус: количество заказов с этим статусом}`.

В таблице заказов отображаются:

- код заказа (`order.code`, например `TN-00001`);
- дата создания;
- клиент (ссылка на `client_detail`);
- телефон клиента;
- принятое оборудование;
- детали заказа;
- список услуг (по многим — через `order.services.all`);
- стоимость услуг (`total_price`);
- аванс (`advance`);
- долг клиента по заказу (`duty`);
- статус (`get_status_display()`);
- действия (просмотр / редактирование / удаление).

#### Создание / редактирование / удаление

- `OrderCreateView` / `OrderUpdateView` используют `OrderForm` и общий шаблон `crm/create.html`.
- После создания — редирект на `/orders/`.
- После редактирования — редирект на страницу просмотра заказа (`/orders/<id>/`).
- `OrderDeleteView` использует шаблон `crm/order_confirm_delete.html` и после удаления редиректит на `/orders/`.

Форма `OrderForm`:

- поля: клиент, оборудование, детали, услуги (множественный выбор), аванс, статус;
- клиент — `<select>` с классом `js-client-select` (удобно подключать JS‑поиск по клиентам);
- `advance` — числовое поле с `min=0`, `step=0.01`.

---

### Услуги

Маршруты:

- `GET /services/` → `ServiceListView`
- `GET /services/create/` → `ServiceCreateView`
- `GET /services/<id>/edit/` → `ServiceUpdateView`
- `POST /services/<id>/delete/` → `ServiceDeleteView`  
  (`http_method_names = ('post',)` — удаление только POST‑ом).

Возможности:

- просмотр списка услуг с указанием категории и стоимости;
- создание/редактирование услуг через `ServiceForm`;
- фильтрация по категории в админке (в пользовательском интерфейсе — простой список).

`ServiceForm`:

- поля: категория, наименование услуги, базовая стоимость;
- проверка уникальности имени услуги с понятным сообщением об ошибке.

---

### Покупки запчастей

Маршруты:

- `GET /purchases/` → `PurchaseListView`
- `GET /purchases/create/` → `PurchaseCreateView`
- `GET /purchases/<id>/` → `PurchaseDetailView`
- `GET /purchases/<id>/edit/` → `PurchaseUpdateView`
- `GET /purchases/<id>/delete/` → `PurchaseDeleteView`

#### Список покупок (`PurchaseListView`, `crm/purchase_list.html`)

- Базовый QuerySet: `Purchase.objects.select_related('order__client')`.
- Пагинация через `BaseListView`.

Статистика:

- `total_purchases` — общее количество покупок.
- `physical_amount_purchase` — количество покупок, привязанных к заказам клиентов‑физлиц.
- `legal_amount_purchase` — то же для юр. лиц.

(Фильтров/поиска в текущей версии нет — только статистика и список.)

#### CRUD

- `PurchaseCreateView` / `PurchaseUpdateView` используют `PurchaseForm`.
- После сохранения редирект на `/purchases/` или `/purchases/<id>/` (для обновления).
- `PurchaseDeleteView` использует шаблон `crm/purchase_confirm_delete.html` и после удаления редиректит на `/purchases/`.

`PurchaseForm`:

- поля: заказ (опционально), магазин, детали покупки, статус (`awaiting_receipt`, `received`, `installed`);
- поле `detail` — `Textarea` с плейсхолдером для подробного описания покупки.

---

## Базовые представления и заголовки форм

В [`base_views.py`](base_views.py):

- `BaseListView(LoginRequiredMixin, ListView)` — общий класс для всех списков (пагинация `QUANTITY_ON_PAGE`).
- `BaseCreateView` / `BaseUpdateView`:
  - добавляют сообщения об успехе (`SuccessMessageMixin`);
  - используют общий шаблон `crm/create.html`;
  - через `NameContextMixin` прокидывают в шаблон переменную `name` (родительный падеж: "клиента", "заказа" и т.д.), чтобы заголовки форм строились автоматически.
- `BaseDetailView` / `BaseDeleteView` — общие базовые классы просмотра и удаления с `LoginRequiredMixin`.

В [`mixins.py`](mixins.py) и [`labels.py`](labels.py):

- `GENITIVE_LABELS` — словарь:
  - `Client: 'клиента'`,
  - `Order: 'заказа'`,
  - `Service: 'услуги'`,
  - `Purchase: 'покупки'`.
- `NameContextMixin.get_context_data()` по модели вьюхи (или форме) находит правильную подпись и кладёт её в контекст как `name`.

Пример использования в шаблоне `crm/create.html`:

```django
<h1>Создание {{ name }}</h1>