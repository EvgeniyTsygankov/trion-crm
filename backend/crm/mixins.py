"""Миксины для приложения CRM-системы."""

from .labels import GENITIVE_LABELS


class NameContextMixin:
    """Добавляет в контекст переменную name из словаря GENITIVE_LABELS."""

    def get_context_data(self, **kwargs):
        """Добавляет в контекст название модели в родительном падеже."""
        context = super().get_context_data(**kwargs)
        model = getattr(self, 'model', None)
        if model is None:
            form = context.get('form')
            if form is not None:
                model = form._meta.model
        if model is not None:
            meta = model._meta
            label = GENITIVE_LABELS.get(model, meta.verbose_name)
            context.setdefault('name', label)
        return context
