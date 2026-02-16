"""URLs del módulo customers."""

from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='list'),
    path('crear/', views.CustomerCreateView.as_view(), name='create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.CustomerUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.CustomerDeleteView.as_view(), name='delete'),
    path('exportar/', views.CustomerExportCSVView.as_view(), name='export_csv'),
]

