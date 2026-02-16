"""Admin del módulo operations."""

from django.contrib import admin
from .models import Operation, OperationItem


class OperationItemInline(admin.TabularInline):
    model = OperationItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal']
    readonly_fields = ['subtotal']


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ['number', 'type', 'date', 'status', 'total', 'company']
    list_filter = ['type', 'status', 'company', 'date']
    search_fields = ['number']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'subtotal', 'tax', 'total']
    raw_id_fields = ['customer', 'supplier', 'company', 'created_by']
    inlines = [OperationItemInline]
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        """Filtra por empresa para usuarios no-superuser."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Para usuarios no-superuser, filtrar por empresa activa
        if hasattr(request, 'current_company') and request.current_company:
            return qs.filter(company=request.current_company)
        return qs.none()


@admin.register(OperationItem)
class OperationItemAdmin(admin.ModelAdmin):
    list_display = ['operation', 'product', 'quantity', 'unit_price', 'subtotal']
    list_filter = ['operation__type', 'operation__company']
    search_fields = ['product__name', 'operation__number']
    readonly_fields = ['subtotal']
    raw_id_fields = ['operation', 'product']
    
    def get_queryset(self, request):
        """Filtra por empresa para usuarios no-superuser."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Para usuarios no-superuser, filtrar por empresa activa a través de operation
        if hasattr(request, 'current_company') and request.current_company:
            return qs.filter(operation__company=request.current_company)
        return qs.none()
