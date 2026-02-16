"""URLs del módulo operations."""

from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    path('', views.OperationListView.as_view(), name='list'),
    path('crear/', views.OperationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.OperationDetailView.as_view(), name='detail'),
    path('<int:pk>/confirmar/', views.OperationConfirmView.as_view(), name='confirm'),
    path('<int:pk>/cancelar/', views.OperationCancelView.as_view(), name='cancel'),
    path('exportar/', views.OperationExportCSVView.as_view(), name='export_csv'),
]
