"""
URL configuration for Pymes Management System.
La ruta del admin se configura en settings.ADMIN_URL (obfuscación en producción).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('core.urls')),
    path('clientes/', include('customers.urls')),
    path('proveedores/', include('suppliers.urls')),
    path('productos/', include('products.urls')),
    path('operaciones/', include('operations.urls')),
    path('reportes/', include('reports.urls')),
    path('configuracion/', include('config_app.urls')),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
