"""Admin del módulo suppliers."""

from django.contrib import admin
from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'email', 'phone', 'active', 'company']
    list_filter = ['active', 'company', 'created_at']
    search_fields = ['code', 'name', 'email', 'tax_id']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    raw_id_fields = ['company', 'created_by']
    
    def get_queryset(self, request):
        """Filtra por empresa para usuarios no-superuser."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Para usuarios no-superuser, filtrar por empresa activa
        if hasattr(request, 'current_company') and request.current_company:
            return qs.filter(company=request.current_company)
        return qs.none()
