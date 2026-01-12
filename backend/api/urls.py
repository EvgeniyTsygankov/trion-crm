"""URL-конфигурация для CRM системы."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClientViewSet, OrderViewSet, PurchaseViewSet

router = DefaultRouter()
router.register('clients', ClientViewSet)
router.register('orders', OrderViewSet)
router.register('purchases', PurchaseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
