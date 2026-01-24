"""Конфигурация URL для CRM проекта."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'auth/login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/', include('api.urls')),
    path('', include('crm.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/schema/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

handler403 = 'tech_support.error_views.permission_denied'
handler404 = 'tech_support.error_views.page_not_found'
handler500 = 'tech_support.error_views.server_error'
