"""
Managers personalizados para filtrado por empresa.
Garantiza que todas las consultas se filtren por empresa para evitar fugas de datos.
"""

from django.db import models
from django.core.exceptions import ValidationError


class CompanyQuerySet(models.QuerySet):
    """QuerySet que permite filtrar automáticamente por empresa."""
    
    def for_company(self, company):
        """Filtra el queryset por empresa."""
        if company is None:
            raise ValidationError('Se requiere una empresa para filtrar.')
        return self.filter(company=company)
    
    def get_or_404_for_company(self, company, **kwargs):
        """Obtiene un objeto o retorna 404, verificando que pertenezca a la empresa."""
        if company is None:
            raise ValidationError('Se requiere una empresa para obtener el objeto.')
        # Asegurar que el filtro de company esté presente
        kwargs.setdefault('company', company)
        obj = self.filter(**kwargs).first()
        if obj is None:
            from django.http import Http404
            raise Http404('El objeto no existe o no pertenece a su empresa.')
        return obj


class CompanyManager(models.Manager):
    """
    Manager que proporciona métodos para filtrar por empresa.
    IMPORTANTE: Este manager NO filtra automáticamente por defecto.
    Las vistas DEBEN usar for_company() explícitamente para filtrar.
    """
    
    def get_queryset(self):
        """Retorna un CompanyQuerySet."""
        return CompanyQuerySet(self.model, using=self._db)
    
    def for_company(self, company):
        """Filtra por empresa. MÉTODO OBLIGATORIO para todas las consultas."""
        if company is None:
            raise ValidationError('Se requiere una empresa para filtrar.')
        return self.get_queryset().for_company(company)
    
    def get_or_404_for_company(self, company, **kwargs):
        """Obtiene un objeto o retorna 404, verificando que pertenezca a la empresa."""
        return self.get_queryset().get_or_404_for_company(company, **kwargs)

