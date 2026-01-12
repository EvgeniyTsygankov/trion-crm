"""
Клиент для обращения к REST API CRM из Telegram-бота.

Содержит:
- функцию get_tokens для получения JWT-токенов по логину и паролю;
- класс CRMClient с методами для чтения клиентов, заказов и покупок;
- обёртку над requests.Session с автоматическим обновлением access-токена
  по refresh-токену и обработкой ошибок.
"""

from http import HTTPStatus

import requests

from .config import API_BASE_URL
from .logger import logger


class CRMClientError(RuntimeError):
    """Базовый класс для всех ошибок клиента CRM-системы."""

    default_message = "Ошибка CRM клиента"

    def __init__(self, message: str | None = None):
        """Инициализирует исключение CRMClientError."""
        super().__init__(message or self.default_message)


class CRMAuthError(CRMClientError):
    """Ошибка аутентификации/авторизации в CRM-системе."""

    default_message = "Пользователь не авторизован"


class RefreshTokenMissingError(CRMAuthError):
    """Ошибка отсутствия refresh-токена."""

    default_message = "Refresh токен отсутствует"


class RefreshTokenInvalidError(CRMAuthError):
    """Ошибка недействительного refresh-токена."""

    default_message = "Refresh токен недействителен"


def get_tokens(username, password):
    """Получает JWT-токены по логину и паролю через API Djoser.

    Отправляет POST-запрос на /api/auth/jwt/create/ с полями username и
    password. При успешном ответе возвращает словарь:
        {'access': <access_token>, 'refresh': <refresh_token>}
    При ошибке авторизации requests.raise_for_status() поднимет HTTPError.
    """
    token_url = f'{API_BASE_URL}/api/auth/jwt/create/'
    payload = {'username': username, 'password': password}
    response = requests.post(token_url, json=payload)
    response.raise_for_status()
    data = response.json()
    return {
        'access': data['access'],
        'refresh': data['refresh'],
    }


class CRMClient:
    """Клиент для обращения к REST API CRM.

    Хранит access- и refresh-токены, использует requests.Session для
    повторного использования соединений и автоматического обновления
    access-токена при истечении срока действия.
    """

    def __init__(self, access, refresh, base_url=API_BASE_URL):
        """Инициализация клиента CRM API."""
        self.access_token = access
        self.refresh_token = refresh
        self.base_url = str(base_url).rstrip('/')
        self.session = requests.Session()
        self.session.headers.update(
            {'Authorization': f'Bearer {self.access_token}'}
        )

    def _refresh(self):
        """Обновить access-токен по refresh-токену."""
        if not self.refresh_token:
            logger.error('Отсутствует refresh-токен при обновлении')
            raise RefreshTokenMissingError
        url = f'{self.base_url}/api/auth/jwt/refresh/'
        payload = {'refresh': self.refresh_token}
        response = self.session.post(url, json=payload)
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            logger.warning('Refresh-токен недействителен')
            raise RefreshTokenInvalidError
        response.raise_for_status()
        data = response.json()
        self.access_token = data['access']
        self.session.headers.update(
            {'Authorization': f'Bearer {self.access_token}'}
        )

    def _request(self, method, path, **kwargs):
        """Сделать запрос к API,при 401 один раз обновить токен и повторить."""
        url = f'{self.base_url}/{path}'
        response = self.session.request(method, url, **kwargs)
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            try:
                self._refresh()
            except CRMAuthError as exc:
                raise CRMAuthError from exc
            response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def _extract_results(self, data):
        """Вернуть список из ответа API: с пагинацией и без."""
        return (
            data['results']
            if (isinstance(data, dict) and 'results' in data)
            else data
        )

    def get_clients(self, search=None):
        """Список клиентов, опционально с поиском по телефону."""
        params = {}
        if search:
            params['search'] = search
        response = self._request('GET', 'api/clients/', params=params)
        data = response.json()
        return self._extract_results(data)

    def get_client(self, client_id):
        """Получить клиента по id."""
        path = f'api/clients/{client_id}/'
        response = self._request('GET', path)
        return response.json()

    def get_orders(self, status=None, search=None, ordering=None):
        """Список заказов с фильтрацией/поиском/сортировкой."""
        params = {}
        if status is not None:
            params['status'] = status
        if search is not None:
            params['search'] = search
        if ordering is not None:
            params['ordering'] = ordering
        response = self._request('GET', 'api/orders/', params=params)
        data = response.json()
        return self._extract_results(data)

    def get_order(self, order_id):
        """Получить заказ по id."""
        path = f'api/orders/{order_id}/'
        response = self._request('GET', path)
        return response.json()

    def get_purchases(self, status=None, search=None, ordering=None):
        """Список покупок (закупок), опционально с фильтрами."""
        params = {}
        if status is not None:
            params['status'] = status
        if search is not None:
            params['search'] = search
        if ordering is not None:
            params['ordering'] = ordering
        response = self._request('GET', 'api/purchases/', params=params)
        data = response.json()
        return self._extract_results(data)

    def get_purchase(self, purchase_id):
        """Получить покупку по id."""
        path = f'api/purchases/{purchase_id}/'
        response = self._request('GET', path)
        return response.json()
