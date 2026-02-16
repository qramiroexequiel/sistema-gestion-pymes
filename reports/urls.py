"""URLs del módulo reports."""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsListView.as_view(), name='list'),
    path('ventas-periodo/', views.SalesByPeriodView.as_view(), name='sales_by_period'),
    path('compras-periodo/', views.PurchasesByPeriodView.as_view(), name='purchases_by_period'),
    path('resumen-clientes/', views.SummaryByCustomerView.as_view(), name='summary_by_customer'),
    path('resumen-proveedores/', views.SummaryBySupplierView.as_view(), name='summary_by_supplier'),
]
