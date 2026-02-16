"""
Modelos del módulo de configuración por empresa.
"""

from django.db import models
from core.models import Company


class CompanySettings(models.Model):
    """Configuración por empresa."""
    
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        verbose_name='Empresa',
        related_name='settings'
    )
    currency = models.CharField('Moneda', max_length=10, default='USD')
    tax_rate_default = models.DecimalField(
        'Tasa de impuesto por defecto (%)',
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    timezone = models.CharField('Zona horaria', max_length=50, default='America/Argentina/Buenos_Aires')
    date_format = models.CharField('Formato de fecha', max_length=20, default='DD/MM/YYYY')
    fiscal_year_start = models.CharField(
        'Inicio del año fiscal',
        max_length=10,
        default='01-01',
        help_text='Formato: MM-DD'
    )
    custom_fields = models.JSONField('Campos personalizados', default=dict, blank=True)
    updated_at = models.DateTimeField('Fecha de actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Empresa'
        verbose_name_plural = 'Configuraciones de Empresa'
    
    def __str__(self):
        return f'Configuración de {self.company.name}'
