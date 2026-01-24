"""Админка Django для управления моделями CRM."""

from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Регистрация модели Category в админ-панели."""

    model = Category
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}  # noqa: RUF012
