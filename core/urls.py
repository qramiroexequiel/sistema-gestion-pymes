"""
URLs del módulo core.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/data/', views.DashboardDataView.as_view(), name='dashboard_data'),
    path('dashboard/export-pdf/', views.ExportDashboardPDFView.as_view(), name='dashboard_pdf_export'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.ProfileView.as_view(), name='profile'),
    path('empresa/seleccionar/', views.CompanySelectView.as_view(), name='company_select'),
]

