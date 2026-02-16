"""
Modelos del módulo de operaciones (ventas y compras unificadas).
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from core.models import CompanyModelMixin
from core.managers import CompanyManager
from customers.models import Customer
from suppliers.models import Supplier
from products.models import Product


class Operation(CompanyModelMixin):
    """Modelo unificado de Operación (Venta/Compra)."""
    
    TYPE_CHOICES = [
        ('sale', 'Venta'),
        ('purchase', 'Compra'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
    ]
    
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    number = models.CharField('Número', max_length=50)
    date = models.DateField('Fecha')
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        verbose_name='Cliente',
        related_name='operations',
        blank=True,
        null=True
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        verbose_name='Proveedor',
        related_name='operations',
        blank=True,
        null=True
    )
    subtotal = models.DecimalField('Subtotal', max_digits=15, decimal_places=2, default=0.00)
    tax = models.DecimalField('Impuesto', max_digits=15, decimal_places=2, default=0.00)
    total = models.DecimalField('Total', max_digits=15, decimal_places=2, default=0.00)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField('Notas', blank=True, null=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        verbose_name='Creado por',
        related_name='operations_created',
        null=True,
        blank=True
    )
    
    objects = CompanyManager()
    
    class Meta:
        verbose_name = 'Operación'
        verbose_name_plural = 'Operaciones'
        unique_together = [['company', 'type', 'number']]
        ordering = ['-date', '-number']
        indexes = [
            models.Index(fields=['company', 'type', '-date']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'type', 'number']),
            models.Index(fields=['company', 'date']),  # Índice compuesto para búsquedas por fecha
            models.Index(fields=['customer']),
            models.Index(fields=['supplier']),
        ]
    
    def clean(self):
        """Valida que la operación tenga cliente o proveedor según su tipo."""
        if self.type == 'sale' and not self.customer:
            raise ValidationError({'customer': 'Una venta debe tener un cliente asociado.'})
        if self.type == 'purchase' and not self.supplier:
            raise ValidationError({'supplier': 'Una compra debe tener un proveedor asociado.'})
        if self.type == 'sale' and self.supplier:
            raise ValidationError({'supplier': 'Una venta no puede tener un proveedor asociado.'})
        if self.type == 'purchase' and self.customer:
            raise ValidationError({'customer': 'Una compra no puede tener un cliente asociado.'})
    
    def save(self, *args, **kwargs):
        """Valida antes de guardar. Los totales se calculan en services."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        type_display = self.get_type_display()
        return f'{type_display} #{self.number} - {self.date}'


class OperationItem(models.Model):
    """Modelo de Item de Operación."""
    
    operation = models.ForeignKey(
        Operation,
        on_delete=models.CASCADE,
        verbose_name='Operación',
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name='Producto/Servicio',
        related_name='operation_items'
    )
    quantity = models.DecimalField('Cantidad', max_digits=12, decimal_places=2)
    unit_price = models.DecimalField('Precio unitario', max_digits=12, decimal_places=2)
    subtotal = models.DecimalField('Subtotal', max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = 'Item de Operación'
        verbose_name_plural = 'Items de Operación'
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        """
        Calcula el subtotal antes de guardar.
        IMPORTANTE: No recalcula totales de la operación aquí.
        Los totales deben recalcularse explícitamente usando services.
        """
        # Calcular subtotal del item (cálculo simple, no lógica de negocio)
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # NO recalcular totales aquí - debe hacerse explícitamente en services
    
    def __str__(self):
        return f'{self.product.name} - {self.quantity} x {self.unit_price}'
