"""Модуль валидаторов для CRM приложения."""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+7\d{10}$',
    message="Номер телефона должен начинаться с '+7' и содержать 11 цифр",
    code='invalid_phone',
)


def validate_company_for_legal(value, entity_type):
    """Проверяет, что поле company заполнено."""
    if entity_type == 'UL' and not (value or '').strip():
        raise ValidationError(
            'Название компании обязательно для юридических лиц',
            code='company_required_for_legal',
        )
