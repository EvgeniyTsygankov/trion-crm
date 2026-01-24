# API CRM system

Приложение `api` предоставляет **read‑only REST API** поверх данных основного приложения `crm`.  
API используется для внешних интеграций и Telegram‑бота: получения информации о клиентах, заказах и покупках запчастей/программного обеспечения.

- Бэкенд: Django REST Framework
- Аутентификация: JWT (SimpleJWT) через Djoser
- Документация: OpenAPI (drf-spectacular) + Swagger UI / ReDoc
- Все ViewSet’ы в `api` — `ReadOnlyModelViewSet` (создание/изменение/удаление через API запрещены)

---

## Базовый URL

В корневом `urls.py` проекта подключение такое:

```python
path('api/', include('api.urls')),
```

Далее во всех примерах предполагается префикс /api/:

- /api/clients/
- /api/orders/
- /api/purchases/

## Аутентификация

API защищено (по умолчанию требуется авторизация).

Заголовок авторизации:
`Authorization: Bearer <access_token>`

Используются эндпоинты Djoser JWT (как в проекте и в Telegram‑боте):

- `POST /api/auth/jwt/create/` — получить `access` + `refresh`
- `POST /api/auth/jwt/refresh/` — обновить `access` по `refresh`

Пример:

```bash
curl -X POST http://127.0.0.1/api/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```
Ответ:

```json
{
  "access": "<JWT_ACCESS_TOKEN>",
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```

## Управление пользователями

Djoser подключён в проекте по api/auth/, но права на операции с пользователями ограничены (в настройках проекта операции вроде user_create/user_list/... разрешены только админам).

## Документация API

Полная и всегда актуальная OpenAPI‑схема и интерактивная документация:

- Swagger UI: `GET /api/schema/swagger-ui/`
- ReDoc: `GET /api/schema/redoc/`
- JSON‑схема: `GET /api/schema/`

Документация генерируется автоматически из сериализаторов и ViewSet’ов с помощью drf-spectacular.

## Роутер

`backend/api/urls.py:`
```python
router = DefaultRouter()
router.register('clients', ClientViewSet)
router.register('orders', OrderViewSet)
router.register('purchases', PurchaseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

Основные маршруты:

- `/api/clients/?search=+7999...` — поиск клиента по номеру телефона
- `/api/clients/{id}/` - клиент по ID
- `/api/orders/` - список заказов (с фильтрацией и поиском)
- `/api/orders/{id}/` - заказ по ID
- `/api/purchases/` - список покупок (с фильтрацией и поиском)
- `/api/purchases/{id}/` - покупка по ID

# Ресурсы и фильтрация

## 1. Клиенты - `/api/clients/`

### Особенность: параметр `search` обязателен

`GET /api/clients/` без `?search=` вернёт 400:

```json
{"detail": "Параметр ?search= обязателен."}
```

### Поиск клиента по телефону

- `GET /api/clients/?search=+79998887766` 

Поиск реализован через SearchFilter по полю `mobile_phone`

Пример:

```bash
curl "http://127.0.0.1/api/clients/?search=+7999" \
  -H "Authorization: Bearer <TOKEN>"
```

### Детальная информация по клиенту

`GET /api/clients/{id}/`

Пример ответа:

```json
{
  "id": 1,
  "client_name": "Иван Петров",
  "mobile_phone": "+79998887766",
  "entity_type": "FL",
  "company": "",
  "address": "г. Москва, ул. Примерная, д.1"
}
```

Поля:

- `id` - идентификатор клиента
- `client_name` - ФИО
- `mobile_phone` - телефон в формате +7XXXXXXXXXX
- `entity_type` - тип лица (FL - физ, UL - юр)
- `company` - название компании (для юр. лиц обязательно на уровне доменной логики)
- `address` - адрес


## 2. Заказы — `/api/orders/`

### Список заказов

`GET /api/orders/`

Оптимизация QuerySet:

- `select_related('client')`
- `prefetch_related('service_lines__service__category')`
- `prefetch_related('purchases')`

### Фильтрация

Поддерживается: `status` — `?status=in_working` / `?status=completed` и т.п.

Пример:

```bash
curl "http://127.0.0.1/api/orders/?status=completed" \
  -H "Authorization: Bearer <TOKEN>"
```
### Поиск

Поиск реализован вручную в `OrderViewSet.get_queryset()`

Поддерживается параметр `?search=`:

- `accepted_equipment__icontains`
- `client__mobile_phone__icontains`
- если в строке поиска есть цифры — дополнительно ищем по `number=int(digits)`
  (точное совпадение)

Примеры:

- `GET /api/orders/?search=+7999`
- `GET /api/orders/?search=iPhone`
- `GET /api/orders/?search=101`
- `GET /api/orders/?search=MA2000`

### Сортировка

OrderingFilter:

- `ordering_fields = ('id',)`
- по умолчанию `ordering = ('-id',)`

Примеры:

- `GET /api/orders/?ordering=id`
- `GET /api/orders/?ordering=-id`

### Детальная информация

`GET /api/orders/{id}/`

Пример ответа (актуальные поля сериализатора):

```json
{
  "id": 10,
  "code": "TN-00010",
  "create": "2026-01-08T12:34:56Z",
  "client_name": "Иван Петров",
  "mobile_phone": "+79998887766",
  "accepted_equipment": "iPhone 12",
  "detail": "Не включается",
  "services": [
    { "id": 5, "service_name": "Диагностика", "amount": "500.00" }
  ],
  "purchases": [
    {
      "id": 3,
      "create": "2026-01-08T13:45:00Z",
      "store": "Ситилинк",
      "detail": "Блок питания, артикул 12345",
      "cost": "1500.00",
      "status": "received"
    }
  ],
  "services_total": "500.00",
  "purchases_total": "1500.00",
  "total_amount": "2000.00",
  "advance": "1000.00",
  "paid": "0.00",
  "duty": "1000.00",
  "status": "in_working"
}
```

Поля (основное):

- `id` - ID заказа
- `code` - код заказа
- `create` - дата/время создания
- `client_name` - ФИО клиента
- `accepted_equipment` - принятое оборудование
- `detail` - описание неисправности
- `services` - вложенный список услуг
  - `id` - ID услуги
  - `service_name` - наименование услуги
  - `amount` - стоимость
- `purchases` - примененный товар (запчасти/ПО)
  - `id` - ID товара
  - `create` - дата/время создания
  - `store` - магазин
  - `detail` - описание товара
  - `cost` - стоимость
  - `status` - статус закупки товара
- `services_total` - сумма всех услуг
- `purchases_total` - сумма всего товара
- `total_amount` - общая сумма (services_total + purchases_total)
- `advance` - аванс
- `paid` - оплачено
- `duty` - баланс клиента = total_amount - advance - paid
- `status` - статус заказа

## 3. Покупки запчастей - `/api/purchases/`

### Список покупок

`GET /api/purchases/`

Оптимизация QuerySet: `select_related('order__client')`.

Покупка может быть без заказа (тогда `order_code` и `client_name` будут `null`).

### Фильтрация

Поддерживается: `status` — `?status=delivery_expected|received|installed`

Пример:

```bash
curl "http://127.0.0.1/api/purchases/?status=received" \
  -H "Authorization: Bearer <TOKEN>"
```

### Поиск

SearchFilter по полю: `detail`

Пример: `GET /api/purchases/?search=память`

### Сортировка

`OrderingFilter`:

- `ordering_fields = ('id',)`
- по умолчанию `ordering = ('-id',)`

### Детальная информация

`GET /api/purchases/{id}/`

Пример ответа:

```json
{
  "id": 3,
  "order_code": "TN-00010",
  "create": "2026-01-08T13:45:00Z",
  "client_name": "Коротков Михаил",
  "store": "Ситилинк",
  "detail": "Блок питания, артикул 12345",
  "cost": "1500.00",
  "status": "received"
}
```

Если покупка без заказа:

- `order_code: null`
- `client_name: null`


Поля:

- `id` - идентификатор покупки
- `order_code` - код заказа (TN-00010) или null, если заказа нет
- `create` - дата создания
- `store` - магазин
- `detail` - описание товара
- `cost` - стоимость
- `status` - статус (ожидается поставка, получено, установлено)

## Ограничения (важно)

`POST/PUT/PATCH/DELETE` для `/api/clients/`, `/api/orders/`, `/api/purchases/` запрещены (read-only API).
Для `/api/clients/` параметр `?search=` обязателен, иначе 400.