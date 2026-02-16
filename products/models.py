"""
Modelos del módulo de productos y servicios.
"""

from django.db import models
from core.models import CompanyModelMixin
from core.managers import CompanyManager


class Product(CompanyModelMixin):
    """Modelo de Producto/Servicio."""
    
    TYPE_CHOICES = [
        ('product', 'Producto'),
        ('service', 'Servicio'),
    ]
    
    code = models.CharField('Código', max_length=50)
    name = models.CharField('Nombre', max_length=200)
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES, default='product')
    description = models.TextField('Descripción', blank=True, null=True)
    price = models.DecimalField('Precio', max_digits=12, decimal_places=2, default=0.00)
    unit_of_measure = models.CharField('Unidad de medida', max_length=20, default='unidad')
    stock = models.DecimalField('Stock', max_digits=12, decimal_places=2, blank=True, null=True)
    active = models.BooleanField('Activo', default=True)
    
    objects = CompanyManager()
    
    class Meta:
        verbose_name = 'Producto/Servicio'
        verbose_name_plural = 'Productos/Servicios'
        unique_together = [['company', 'code']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'active']),
            models.Index(fields=['company', 'code']),
            models.Index(fields=['company', 'type']),
            models.Index(fields=['company', 'name']),  # Índice compuesto para búsquedas
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f'{self.code} - {self.name}'
