"""Admin del módulo config_app."""

from django.contrib import admin
from .models import CompanySettings


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ['company', 'currency', 'tax_rate_default', 'timezone', 'updated_at']
    search_fields = ['company__name']
    readonly_fields = ['updated_at']
    raw_id_fields = ['company']
