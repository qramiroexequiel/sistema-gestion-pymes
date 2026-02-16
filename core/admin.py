"""
Admin del módulo core.
"""

from django.contrib import admin
from .models import Company, Membership, AuditLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'tax_id', 'email', 'is_demo', 'active', 'created_at']
    list_filter = ['active', 'is_demo', 'created_at']
    search_fields = ['name', 'tax_id', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'tax_id', 'email', 'phone', 'address', 'logo')
        }),
        ('Estado', {
            'fields': ('active', 'is_demo')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'role', 'active', 'created_at']
    list_filter = ['role', 'active', 'created_at']
    search_fields = ['user__username', 'user__email', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Filtra por empresa para usuarios no-superuser."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Para usuarios no-superuser, solo ver sus propias memberships
        return qs.filter(user=request.user)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'action', 'model_name', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'company__name', 'model_name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        """Filtra por empresa para usuarios no-superuser."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Para usuarios no-superuser, filtrar por empresa activa
        if hasattr(request, 'current_company') and request.current_company:
            return qs.filter(company=request.current_company)
        return qs.none()
