"""URLs del módulo suppliers."""

from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.SupplierListView.as_view(), name='list'),
    path('crear/', views.SupplierCreateView.as_view(), name='create'),
    path('<int:pk>/', views.SupplierDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.SupplierUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.SupplierDeleteView.as_view(), name='delete'),
    path('exportar/', views.SupplierExportCSVView.as_view(), name='export_csv'),
]
