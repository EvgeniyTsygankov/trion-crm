"""Базовые представления для CRM проекта."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .constants import QUANTITY_ON_PAGE
from .mixins import NameContextMixin


class BaseListView(LoginRequiredMixin, ListView):
    """Базовый ListView для всех списков CRM."""

    paginate_by = QUANTITY_ON_PAGE


class BaseCreateView(
    LoginRequiredMixin, NameContextMixin, SuccessMessageMixin, CreateView
):
    """Базовый CreateView для авторизованных пользователей."""

    template_name = 'crm/create.html'


class BaseUpdateView(
    LoginRequiredMixin, NameContextMixin, SuccessMessageMixin, UpdateView
):
    """Базовый UpdateView для авторизованных пользователей."""

    template_name = 'crm/create.html'


class BaseDetailView(LoginRequiredMixin, DetailView):
    """Базовый DetailView для авторизованных пользователей."""

    pass


class BaseDeleteView(LoginRequiredMixin, DeleteView):
    """Базовый DeleteView для авторизованных пользователей."""

    pass
