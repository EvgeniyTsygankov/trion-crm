# API CRM system

Приложение `api` предоставляет **read‑only REST API** поверх данных основного приложения `crm`.  
API используется для внешних интеграций и Telegram‑бота: получения информации о клиентах, заказах и покупках запчастей.

- Бэкенд: Django REST Framework
- Аутентификация: JWT (djangorestframework-simplejwt)
- Документация: OpenAPI 3.0 (drf-spectacular) + Swagger UI / ReDoc

> Все ViewSet’ы в этом приложении — `ReadOnlyModelViewSet`:  
> API не создаёт/не изменяет данные, только читает их.

---

## Базовый URL

В корневом `urls.py` проекта приложение обычно подключается так:

```python
path('api/', include('api.urls')),
```

Далее во всех примерах предполагается префикс /api/:

/api/clients/
/api/orders/
/api/purchases/
и т.д.

## Аутентификация

Во всех защищённых эндпоинтах используется JWT‑аутентификация.

Заголовок авторизации:
`Authorization: Bearer <access_token>`

Эндпоинты выдачи токенов (см. корневой urls.py, пример):
- POST /api/token/ - получить пару access + refresh
- POST /api/token/refresh/ - обновить access по refresh

Пример:

```python
POST /api/token/
Content-Type: application/json
```
```json
{
  "username": "user@example.com",
  "password": "password123"
}

{
  "access": "<JWT_ACCESS_TOKEN>",
  "refresh": "<JWT_REFRESH_TOKEN>"
}
```

## Документация API

Полная и всегда актуальная OpenAPI‑схема и интерактивная документация:

- Swagger UI: GET /api/schema/swagger-ui/
- ReDoc: GET /api/schema/redoc/
- JSON‑схема: GET /api/schema/

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

- /api/clients/?search=+7999... — поиск клиента по номеру телефона
- /api/clients/{id}/ - клиент по ID
- /api/orders/ - список заказов (с фильтрацией и поиском)
- /api/orders/{id}/ - заказ по ID
- /api/purchases/ - список покупок (с фильтрацией и поиском)
- /api/purchases/{id}/ - покупка по ID

# Ресурсы и фильтрация

## 1. Клиенты - ClientViewSet

URL‑ы
- `GET /api/clients/?search=+7999...` — поиск клиента по номеру телефона  
  (параметр `search` обязателен, без него вернётся 400)
- `GET /api/clients/{id}/` — детальная информация о клиенте по ID

Сериализатор: `ClientSerializer`

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

- 'id' - идентификатор клиента
- 'client_name' - имя
- 'mobile_phone' - телефон в формате +7XXXXXXXXXX
- 'entity_type' - тип лица (FL - физ, UL - юр)
- 'company' - название компании (для юр. лиц обязательно на уровне доменной логики)
- 'address' - адрес

**Фильтрация и поиск**

ViewSet:

```python
class ClientViewSet(ReadOnlyModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('mobile_phone',)
```
- Поиск по телефону: SearchFilter с полем mobile_phone.
- Параметр: ?search=...

Примеры:

```
GET /api/clients/?search=+7999
Authorization: Bearer <token>
Accept: application/json
```

## 2. Заказы — OrderViewSet

URL‑ы

- 'GET /api/orders/'
- 'GET /api/orders/{id}/'

Сериализатор: `OrderSerializer`

```json
{
  "id": 10,
  "code": "TN-00010",
  "number": 10,
  "client": 1,
  "client_name": "Иван Петров",
  "create": "2026-01-08T12:34:56Z",
  "accepted_equipment": "iPhone 12, черный",
  "detail": "Не включается",
  "services": [
    {
      "id": 5,
      "category": "remont-smartfonov",
      "service_name": "Диагностика",
      "amount": "500.00"
    }
  ],
  "advance": "1000.00",
  "status": "in_working",
  "total_price": "500.00",
  "duty": "-500.00"
}
```

Поля (основное):

- Идентификаторы:
  - 'id' - ID заказа
  - code - код вида TN-00010
  - number - числовой номер
- Клиент:
  - client - ID клиента
  - client_name - имя клиента
- Дата и описание:
  - create - дата/время создания
  - accepted_equipment - принятое оборудование
  - detail - детали заказа
- Услуги:
  - services - вложенный список услуг (ServiceSerializer, read-only)
- Финансы:
  - advance - аванс
  - status - статус (OrderStatus)
  - total_price - суммарная стоимость услуг
  - duty - баланс = total_price - advance

**Оптимизация запросов**

```python
queryset = Order.objects.select_related('client').prefetch_related(
    'services', 'services__category'
)
```
- select_related('client') - подтягивает клиента одним запросом.
- prefetch_related('services', 'services__category') - предзагрузка услуг и их категорий.

**Фильтрация, поиск, сортировка**

```python
filter_backends = (
    DjangoFilterBackend,
    filters.SearchFilter,
    filters.OrderingFilter,
)
filterset_fields = ('status',)
search_fields = (
    'accepted_equipment',
    'client__mobile_phone',
    'number',
)
ordering_fields = ('id',)
ordering = ('-id',)
```

Поддерживается:

1. **Фильтр по статусу**

Параметр: `?status=<значение>` (например, in_working, completed и т.п., см. OrderStatus).

```
GET /api/orders/?status=completed
Authorization: Bearer <token>
```

2. Поиск

`SearchFilter` с параметром `?search=` по полям:
   - accepted_equipment - текст оборудования;
   - client__mobile_phone - телефон клиента;
   - number - номер заказа (как строка).

```
GET /api/orders/?search=+7999
GET /api/orders/?search=iPhone
GET /api/orders/?search=10
```

3. Сортировка

`OrderingFilter` с параметром `?ordering=` по полю id:
   - `?ordering=id` - по возрастанию ID;
   - `?ordering=-id` - по убыванию ID (значение по умолчанию).

```
GET /api/orders/?ordering=id
GET /api/orders/?status=in_working&ordering=-id
```

## 3. Покупки запчастей - PurchaseViewSet

URL‑ы

- 'GET /api/purchases/'
- 'GET /api/purchases/{id}/'

Сериализатор: 'PurchaseSerializer'

```json
{
  "id": 3,
  "order": 10,
  "order_code": "TN-00010",
  "create": "2026-01-08T13:45:00Z",
  "store": "Ситилинк",
  "detail": "Блок питания, артикул 12345, цена 1500 руб.",
  "status": "received"
}
```

Поля:

- id - идентификатор покупки
- order - ID связанного заказа (может быть null)
- order_code - код заказа (TN-00010) или null, если заказа нет
- create - дата создания
- store - магазин
- detail - детали покупки
- status - статус (awaiting_receipt, received, installed)

**Оптимизация запросов**

```python
queryset = Purchase.objects.select_related('order')
```

Фильтрация, поиск, сортировка

```python
filter_backends = (
    DjangoFilterBackend,
    filters.SearchFilter,
    filters.OrderingFilter,
)
filterset_fields = ('status',)
search_fields = ('detail',)
ordering_fields = ('id',)
ordering = ('-id',)
```

Поддерживается:

1. **Фильтр по статусу**

`GET /api/purchases/?status=awaiting_receipt`

2. **Поиск по деталям покупки** ('detail', регистр не учитывается):

`GET /api/purchases/?search=блок питания`

3. **Сортировка по ID** (как и в заказах):

```
GET /api/purchases/?ordering=id
GET /api/purchases/?ordering=-id  # по умолчанию
```