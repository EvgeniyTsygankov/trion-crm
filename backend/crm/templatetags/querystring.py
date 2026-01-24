"""Модуль для работы с URL-параметрами в шаблонах Django."""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs) -> str:
    """Тег шаблона для работы с параметрами строки запроса URL."""
    request = context['request']
    query = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()
