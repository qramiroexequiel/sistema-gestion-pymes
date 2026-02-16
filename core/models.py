"""
Modelos base del sistema.
Incluye Company, Membership y AuditLog para el sistema multi-tenant.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Company(models.Model):
    """Modelo de Empresa para el sistema multi-tenant."""
    
    name = models.CharField('Nombre', max_length=200)
    tax_id = models.CharField('CUIT/RUT/NIT', max_length=50, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    phone = models.CharField('Teléfono', max_length=50, blank=True, null=True)
    address = models.TextField('Dirección', blank=True, null=True)
    logo = models.ImageField('Logo', upload_to='companies/logos/', blank=True, null=True)
    active = models.BooleanField('Activa', default=True)
    is_demo = models.BooleanField('Empresa Demo', default=False, help_text='Marcar si es una empresa de demostración')
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']
        indexes = [
            models.Index(fields=['active']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name


class Membership(models.Model):
    """Modelo de Membresía que asocia usuarios con empresas y roles."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gestor'),
        ('operator', 'Operador'),
        ('viewer', 'Visualizador'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField('Rol', max_length=20, choices=ROLE_CHOICES, default='operator')
    active = models.BooleanField('Activa', default=True)
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Membresía'
        verbose_name_plural = 'Membresías'
        unique_together = [['user', 'company']]
        indexes = [
            models.Index(fields=['user', 'active']),
            models.Index(fields=['company', 'active']),
        ]
    
    def __str__(self):
        return f'{self.user.username} - {self.company.name} ({self.get_role_display()})'


class AuditLog(models.Model):
    """Modelo de auditoría para registrar acciones del sistema."""
    
    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('view', 'Ver'),
        ('login', 'Iniciar sesión'),
        ('logout', 'Cerrar sesión'),
        ('security_alert', 'Alerta de seguridad'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField('Acción', max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField('Modelo', max_length=100)
    object_id = models.CharField('ID del objeto', max_length=100, blank=True, null=True)
    changes = models.JSONField('Cambios', default=dict, blank=True)
    timestamp = models.DateTimeField('Fecha y hora', auto_now_add=True)
    ip_address = models.GenericIPAddressField('Dirección IP', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Log de auditoría'
        verbose_name_plural = 'Logs de auditoría'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['company', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
        ]
    
    def __str__(self):
        return f'{self.get_action_display()} - {self.model_name} - {self.timestamp}'


class CompanyManagerMixin:
    """Mixin para managers que requieren filtrar por empresa."""
    
    def for_company(self, company):
        """Filtra queryset por empresa."""
        return self.filter(company=company)


class CompanyModelMixin(models.Model):
    """
    Mixin para modelos que pertenecen a una empresa.
    
    Garantiza:
    - company es obligatorio (null=False, blank=False)
    - Índice base en company para optimización de queries
    """
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name='Empresa',
        related_name='%(class)s_set',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Fecha de actualización', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Creado por',
        related_name='%(class)s_created'
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['company']),
        ]
