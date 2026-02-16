"""
Modelos del módulo de proveedores.
"""

from django.db import models
from core.models import CompanyModelMixin
from core.managers import CompanyManager


class Supplier(CompanyModelMixin):
    """Modelo de Proveedor."""
    
    code = models.CharField('Código', max_length=50)
    name = models.CharField('Nombre', max_length=200)
    tax_id = models.CharField('CUIT/RUT/NIT', max_length=50, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    phone = models.CharField('Teléfono', max_length=50, blank=True, null=True)
    address = models.TextField('Dirección', blank=True, null=True)
    notes = models.TextField('Notas', blank=True, null=True)
    active = models.BooleanField('Activo', default=True)
    
    objects = CompanyManager()
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        unique_together = [['company', 'code']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'active']),
            models.Index(fields=['company', 'code']),
            models.Index(fields=['company', 'name']),  # Índice compuesto para búsquedas
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f'{self.code} - {self.name}'
