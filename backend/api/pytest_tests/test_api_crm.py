"""
Модуль тестирования API для CRM-системы.

Содержит тесты для проверки работы API клиентов, заказов и покупок.
"""

from decimal import Decimal
from http import HTTPStatus

import pytest
from rest_framework.test import APIClient

from conftest import (
    create_crm_orders_and_purchases,
    create_test_user,
    get_results,
    setup_api_client_with_auth,
    teardown_api_client_auth,
)
from crm.models import Client


class BaseAPITest:
    """Базовый класс для тестов API с JWT-аутентификацией."""

    def setup_auth(self):
        """Настраивает аутентификацию для теста."""
        self.api = APIClient()
        self.user = create_test_user()
        setup_api_client_with_auth(self.api, self.user)

    def teardown_auth(self):
        """Очищает аутентификацию после теста."""
        teardown_api_client_auth(self.api)


@pytest.mark.django_db
class TestClientAPI(BaseAPITest):
    """Тестирование операций чтения API клиентов."""

    def setup_method(self):
        """Подготовка перед каждым тестом."""
        self.setup_auth()
        self.client1 = Client.objects.create(
            client_name='Иван',
            mobile_phone='+79998887766',
            entity_type='FL',
        )

    def teardown_method(self):
        """Очистка после каждого теста."""
        self.teardown_auth()

    def test_client_list(self):
        """Проверяет получение списка клиентов.

        GET /api/clients/
        """
        resp = self.api.get('/api/clients/')
        assert (
            resp.status_code == HTTPStatus.OK
        ), 'Статус ответа при запросе списка клиентов должен быть 200 OK'

        data = get_results(resp.json())
        client_ids = [client['id'] for client in data]
        assert (
            self.client1.id in client_ids
        ), 'Созданный клиент должен присутствовать в списке'

    def test_client_detail(self):
        """Проверяет получение детальной информации о клиенте.

        GET /api/clients/{id}/
        """
        resp = self.api.get(f'/api/clients/{self.client1.id}/')
        assert (
            resp.status_code == HTTPStatus.OK
        ), 'Статус ответа при запросе деталей клиента должен быть 200 OK'

        data = resp.json()
        assert (
            data['mobile_phone'] == self.client1.mobile_phone
        ), f'Номер телефона должен быть {self.client1.mobile_phone}'

    def test_client_search_by_phone(self):
        """Проверяет поиск клиента по номеру телефона.

        GET /api/clients/?search=...
        """
        resp = self.api.get(
            '/api/clients/', {'search': self.client1.mobile_phone}
        )
        assert (
            resp.status_code == HTTPStatus.OK
        ), 'Статус ответа при поиске клиента по телефону должен быть 200 OK'

        data = get_results(resp.json())
        assert (
            len(data) == 1
        ), f'Должен быть ровно один клиент, найдено {len(data)}'
        assert (
            data[0]['mobile_phone'] == self.client1.mobile_phone
        ), f'Номер телефона должен быть {self.client1.mobile_phone}'
        assert (
            data[0]['id'] == self.client1.id
        ), 'ID найденного клиента должен совпадать с ID созданного клиента'


# --------- Заказы ---------
@pytest.mark.django_db
class TestOrderAPI(BaseAPITest):
    """Тестирование операций чтения API заказов."""

    def setup_method(self):
        """Подготовка перед каждым тестом.

        Инициализирует API-клиент и создаёт тестовые данные.
        """
        self.setup_auth()
        self.data = create_crm_orders_and_purchases()
        self.client1 = self.data['client1']
        self.client2 = self.data['client2']
        self.order1 = self.data['order1']
        self.order2 = self.data['order2']
        self.order3 = self.data['order3']

    def teardown_method(self):
        """Очистка после каждого теста."""
        self.teardown_auth()

    def test_order_list(self):
        """Проверяет получение списка всех заказов.

        GET /api/orders/
        """
        resp = self.api.get('/api/orders/')
        assert (
            resp.status_code == HTTPStatus.OK
        ), 'Статус ответа при запросе списка заказов должен быть 200 OK'

        data = get_results(resp.json())
        returned_ids = {item['id'] for item in data}

        assert (
            self.order1.id in returned_ids
        ), f'Заказ c id={self.order1.id} должен присутствовать в списке'
        assert (
            self.order2.id in returned_ids
        ), f'Заказ c id={self.order2.id} должен присутствовать в списке'
        assert (
            self.order3.id in returned_ids
        ), f'Заказ c id={self.order3.id} должен присутствовать в списке'

    def test_order_detail(self):
        """Проверяет получение детальной информации о заказе.

        GET /api/orders/{id}/
        """
        order = self.order1
        resp = self.api.get(f'/api/orders/{order.id}/')
        assert resp.status_code == HTTPStatus.OK, (
            f'Статус ответа при запросе деталей заказа {order.id} '
            'должен быть 200 OK'
        )

        data = resp.json()

        # Основные поля
        assert (
            data['id'] == order.id
        ), 'Поле id в ответе должно совпадать с id объекта в БД'
        assert (
            data['number'] == order.number
        ), 'Поле number в ответе должно совпадать с номером заказа в БД'
        assert (
            data['client'] == order.client.id
        ), 'Поле client в ответе должно содержать id клиента из БД'
        assert (
            data['accepted_equipment'] == order.accepted_equipment
        ), 'Поле accepted_equipment в ответе должно совпадать с данными в БД'
        assert (
            data['detail'] == order.detail
        ), 'Поле detail в ответе должно совпадать с данными в БД'

        # Вычисляемые поля
        assert Decimal(data['total_price']) == order.total_price, (
            'Поле total_price в ответе должно совпадать с рассчитанной '
            'суммой услуг заказа'
        )
        assert Decimal(data['duty']) == order.duty, (
            'Поле duty в ответе должно совпадать с рассчитанным долгом '
            '(total_price - advance)'
        )
        assert (
            data['code'] == order.code
        ), 'Поле code в ответе должно совпадать с вычисленным кодом заказа'

        # Связанные услуги
        assert len(data['services']) == order.services.count(), (
            'Количество услуг в ответе должно совпадать с количеством '
            'связанных услуг в БД'
        )
        service_names = {s['service_name'] for s in data['services']}
        assert (
            self.data['service1'].service_name in service_names
        ), 'Услуга service1 должна присутствовать в списке услуг заказа'
        assert (
            self.data['service2'].service_name in service_names
        ), 'Услуга service2 должна присутствовать в списке услуг заказа'

    def test_order_filter_by_status(self):
        """Проверяет фильтрацию заказов по статусу.

        GET /api/orders/?status=...
        """
        resp = self.api.get('/api/orders/', {'status': 'completed'})
        assert resp.status_code == HTTPStatus.OK, (
            'Статус ответа при фильтрации заказов по статусу "completed" '
            'должен быть 200 OK'
        )

        data = get_results(resp.json())
        assert (
            data
        ), 'Фильтр по статусу "completed" должен вернуть хотя бы один заказ'
        assert all(
            order['status'] == 'completed' for order in data
        ), 'Все заказы в ответе должны иметь статус "completed"'

    def test_order_post_not_allowed(self):
        """Проверяет, что создание заказа запрещено (ReadOnlyModelViewSet).

        POST /api/orders/
        """
        resp = self.api.post('/api/orders/', {})
        assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
            'Метод POST должен быть запрещён для эндпоинта /api/orders/ '
            '(используется ReadOnlyModelViewSet)'
        )


@pytest.mark.django_db
class TestPurchaseAPI(BaseAPITest):
    """Тестирование операций чтения API покупок."""

    def setup_method(self):
        """Подготовка перед каждым тестом.

        Инициализирует API-клиент и создаёт тестовые данные покупок.
        """
        self.setup_auth()
        self.data = create_crm_orders_and_purchases()
        self.order1 = self.data['order1']
        self.order2 = self.data['order2']
        self.purchase1 = self.data['purchase1']
        self.purchase2 = self.data['purchase2']
        self.purchase3 = self.data['purchase3']
        self.purchase_orphan = self.data['purchase_orphan']

    def teardown_method(self):
        """Очистка после каждого теста."""
        self.teardown_auth()

    def test_purchase_list(self):
        """Проверяет получение списка всех покупок.

        GET /api/purchases/
        """
        resp = self.api.get('/api/purchases/')
        assert (
            resp.status_code == HTTPStatus.OK
        ), 'Статус ответа при запросе списка покупок должен быть 200 OK'

        data = get_results(resp.json())
        returned_ids = {item['id'] for item in data}

        assert (
            self.purchase1.id in returned_ids
        ), f'Покупка с id={self.purchase1.id} должна присутствовать в списке'
        assert (
            self.purchase2.id in returned_ids
        ), f'Покупка с id={self.purchase2.id} должна присутствовать в списке'
        assert (
            self.purchase3.id in returned_ids
        ), f'Покупка с id={self.purchase3.id} должна присутствовать в списке'
        assert self.purchase_orphan.id in returned_ids, (
            f'Покупка с id={self.purchase_orphan.id} (без заказа) должна '
            'присутствовать в списке'
        )

    def test_purchase_detail(self):
        """Проверяет получение детальной информации о покупке с заказом.

        GET /api/purchases/{id}/
        """
        purchase = self.purchase1
        order = purchase.order

        resp = self.api.get(f'/api/purchases/{purchase.id}/')
        assert resp.status_code == HTTPStatus.OK, (
            f'Статус ответа при запросе деталей покупки {purchase.id} '
            'должен быть 200 OK'
        )

        data = resp.json()

        assert (
            data['id'] == purchase.id
        ), 'Поле id в ответе должно совпадать с id покупки в БД'
        assert (
            data['order'] == order.id
        ), 'Поле order в ответе должно содержать id связанного заказа'
        assert (
            data['order_code'] == order.code
        ), 'Поле order_code в ответе должно содержать код связанного заказа'
        assert data['store'] == purchase.store, (
            'Поле store в ответе должно совпадать с наименованием магазина '
            'в БД'
        )
        assert (
            data['detail'] == purchase.detail
        ), 'Поле detail в ответе должно совпадать с деталями покупки в БД'
        assert (
            data['status'] == purchase.status
        ), 'Поле status в ответе должно совпадать со статусом покупки в БД'

    def test_purchase_detail_without_order(self):
        """Проверяет получение детальной информации о покупке без заказа.

        GET /api/purchases/{id}/
        """
        purchase = self.purchase_orphan

        resp = self.api.get(f'/api/purchases/{purchase.id}/')
        assert resp.status_code == HTTPStatus.OK, (
            f'Статус ответа при запросе покупки {purchase.id} без заказа '
            'должен быть 200 OK'
        )

        data = resp.json()
        assert (
            data['id'] == purchase.id
        ), 'Поле id в ответе должно совпадать с id покупки в БД'
        assert (
            data['order'] is None
        ), 'Для покупки без заказа поле order в ответе должно быть null'
        assert (
            data['order_code'] is None
        ), 'Для покупки без заказа поле order_code в ответе должно быть null'

    def test_purchase_filter_by_status(self):
        """Проверяет фильтрацию покупок по статусу.

        GET /api/purchases/?status=...
        """
        resp = self.api.get('/api/purchases/', {'status': 'received'})
        assert resp.status_code == HTTPStatus.OK, (
            'Статус ответа при фильтрации покупок по статусу "received" '
            'должен быть 200 OK'
        )

        data = get_results(resp.json())
        assert (
            data
        ), 'Фильтр по статусу "received" должен вернуть хотя бы одну покупку'
        assert all(
            p['status'] == 'received' for p in data
        ), 'Все покупки в ответе должны иметь статус "received"'

    def test_purchase_ordering(self):
        """Проверяет сортировку покупок по идентификатору.

        GET /api/purchases/?ordering=id
        """
        resp = self.api.get('/api/purchases/', {'ordering': 'id'})
        assert (
            resp.status_code == HTTPStatus.OK
        ), 'Статус ответа при сортировке покупок по id должен быть 200 OK'

        data = get_results(resp.json())
        ids = [p['id'] for p in data]
        assert ids == sorted(ids), (
            'Покупки в ответе должны быть отсортированы по id по возрастанию '
            '(ordering=id)'
        )

    def test_purchase_post_not_allowed(self):
        """Проверяет, что создание покупки запрещено (ReadOnlyModelViewSet).

        POST /api/purchases/
        """
        resp = self.api.post('/api/purchases/', {})
        assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
            'Метод POST должен быть запрещён для эндпоинта /api/purchases/ '
            '(используется ReadOnlyModelViewSet)'
        )
