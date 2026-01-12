"""Марштуты для приложения CRM."""

from django.urls import path

from .views import (
    ClientCreateView,
    ClientDeleteView,
    ClientDetailView,
    ClientListView,
    ClientUpdateView,
    HomeView,
    OrderCreateView,
    OrderDeleteView,
    OrderDetailView,
    OrderListView,
    OrderUpdateView,
    PurchaseCreateView,
    PurchaseDeleteView,
    PurchaseDetailView,
    PurchaseListView,
    PurchaseUpdateView,
    ServiceCreateView,
    ServiceDeleteView,
    ServiceListView,
    ServiceUpdateView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('clients/', ClientListView.as_view(), name='client_list'),
    path('clients/create/', ClientCreateView.as_view(), name='client_create'),
    path(
        'clients/<int:pk>/', ClientDetailView.as_view(), name='client_detail'
    ),
    path(
        'clients/<int:pk>/edit/',
        ClientUpdateView.as_view(),
        name='client_edit',
    ),
    path(
        'clients/<int:pk>/delete/',
        ClientDeleteView.as_view(),
        name='client_delete',
    ),
    path('services/', ServiceListView.as_view(), name='service_list'),
    path(
        'services/create/', ServiceCreateView.as_view(), name='service_create'
    ),
    path(
        'services/<int:pk>/edit/',
        ServiceUpdateView.as_view(),
        name='service_edit',
    ),
    path(
        'services/<int:pk>/delete/',
        ServiceDeleteView.as_view(),
        name='service_delete',
    ),
    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/create/', OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path(
        'orders/<int:pk>/edit/', OrderUpdateView.as_view(), name='order_edit'
    ),
    path(
        'orders/<int:pk>/delete/',
        OrderDeleteView.as_view(),
        name='order_delete',
    ),
    path('purchases/', PurchaseListView.as_view(), name='purchase_list'),
    path(
        'purchases/create/',
        PurchaseCreateView.as_view(),
        name='purchase_create',
    ),
    path(
        'purchases/<int:pk>/',
        PurchaseDetailView.as_view(),
        name='purchase_detail',
    ),
    path(
        'purchases/<int:pk>/edit/',
        PurchaseUpdateView.as_view(),
        name='purchase_edit',
    ),
    path(
        'purchases/<int:pk>/delete/',
        PurchaseDeleteView.as_view(),
        name='purchase_delete',
    ),
]
