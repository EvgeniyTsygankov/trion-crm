"""Конфигурация приложения CRM для Django."""

from django.apps import AppConfig


class CrmConfig(AppConfig):
    """Класс конфигурации приложения CRM."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
