"""URLs del módulo products."""

from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('crear/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.ProductUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.ProductDeleteView.as_view(), name='delete'),
    path('exportar/', views.ProductExportCSVView.as_view(), name='export_csv'),
]
