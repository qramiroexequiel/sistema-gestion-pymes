"""
Mixins para views que requieren acceso a empresa.
Garantizan filtrado por empresa y previenen fugas de datos.
"""

import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.http import Http404
from core.models import Company
from core.constants import ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR, ROLE_VIEWER, ROLE_CHOICES
from core.utils.request import get_client_ip

logger = logging.getLogger('security')


class CompanyRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere que el usuario tenga una empresa asociada.
    
    Reglas uniformes:
    - Si usuario autenticado pero sin current_company → redirige a selección de empresa
    - Si no tiene memberships válidas → cierra sesión y muestra mensaje neutro
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga una empresa activa."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Verificar que el middleware haya establecido la empresa
        if not hasattr(request, 'current_company') or not request.current_company:
            # Si no hay empresa, verificar si el usuario tiene empresas
            from core.models import Membership
            from django.shortcuts import redirect
            from django.contrib import messages
            from django.contrib.auth import logout
            
            # Verificar memberships activas (con empresa activa)
            has_memberships = Membership.objects.filter(
                user=request.user,
                active=True,
                company__active=True
            ).exists()
            
            if has_memberships:
                # Tiene empresas pero no hay selección → redirigir a selección
                messages.info(request, 'Debe seleccionar una empresa para continuar.')
                return redirect('core:company_select')
            else:
                # No tiene memberships válidas → cerrar sesión
                logout(request)
                messages.info(request, 'Su sesión ha finalizado. No tiene empresas asociadas activas.')
                return redirect('core:login')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_company(self):
        """Retorna la empresa actual del request."""
        return self.request.current_company


# Alias para compatibilidad y claridad
TenantRequiredMixin = CompanyRequiredMixin


class RoleRequiredMixin:
    """Mixin que requiere un rol específico en la empresa actual."""
    
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        """Verifica que el usuario tenga el rol requerido."""
        if not request.user.is_authenticated:
            from django.contrib.auth.mixins import AccessMixin
            return AccessMixin().handle_no_permission()
        
        if not hasattr(request, 'current_membership') or not request.current_membership:
            raise PermissionDenied('No tiene una membresía activa en esta empresa.')
        
        if self.required_roles and request.current_membership.role not in self.required_roles:
            roles_display = ', '.join([dict(ROLE_CHOICES).get(r, r) for r in self.required_roles])
            raise PermissionDenied(f'Se requiere uno de los siguientes roles: {roles_display}')
        
        return super().dispatch(request, *args, **kwargs)


class CompanyContextMixin:
    """Mixin que añade la empresa actual al contexto."""
    
    def get_context_data(self, **kwargs):
        """Añade la empresa actual al contexto."""
        context = super().get_context_data(**kwargs)
        context['current_company'] = self.request.current_company
        context['current_membership'] = self.request.current_membership
        return context
    
    def get_client_ip(self):
        """Obtiene la IP del cliente desde request."""
        from core.utils.request import get_client_ip
        return get_client_ip(self.request)


class HTMXResponseMixin:
    """
    Mixin para detectar requests HTMX y devolver templates parciales.
    Las vistas que usen este mixin deben definir:
    - template_name: template completo
    - partial_template_name: template parcial (opcional, se infiere si no se define)
    """
    
    def get_template_names(self):
        """Retorna template parcial si es request HTMX, completo si no."""
        if self.is_htmx_request():
            # Si se define partial_template_name, usarlo
            if hasattr(self, 'partial_template_name'):
                return [self.partial_template_name]
            # Si no, inferir del template_name agregando _partial
            if hasattr(self, 'template_name'):
                base_name = self.template_name.replace('.html', '')
                return [f'{base_name}_partial.html']
        # Request normal, usar template completo (delegar al parent)
        if hasattr(super(), 'get_template_names'):
            return super().get_template_names()
        # Fallback si no hay parent con get_template_names
        if hasattr(self, 'template_name'):
            return [self.template_name]
        return []
    
    def is_htmx_request(self):
        """Verifica si el request viene de HTMX."""
        return self.request.headers.get('HX-Request') == 'true'
    
    def get_context_data(self, **kwargs):
        """Añade flag HTMX al contexto."""
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else kwargs
        context['is_htmx'] = self.is_htmx_request()
        return context


class CompanyFilterMixin:
    """
    Mixin que fuerza el filtrado por empresa en get_queryset().
    OBLIGATORIO para todas las ListView y views que usen querysets.
    IMPOSIBLE de omitir - siempre filtra por empresa antes de aplicar otros filtros.
    PRESERVA optimizaciones del queryset (select_related, prefetch_related, annotations).
    """
    
    def get_queryset(self):
        """
        Fuerza el filtrado por empresa actual ANTES de cualquier otro filtro.
        PRESERVA el queryset existente con sus optimizaciones (select_related/prefetch/annotations).
        """
        company = self.get_company()
        
        if company is None:
            # Si no hay empresa, retornar queryset vacío
            queryset_base = super().get_queryset()
            return queryset_base.none()
        
        # OBTENER queryset base (preserva select_related/prefetch/annotations del parent)
        queryset_base = super().get_queryset()
        
        # Filtrar sobre queryset_base SIN reconstruir desde el manager
        # Esto preserva todas las optimizaciones del queryset
        if hasattr(queryset_base, 'for_company'):
            # Si el queryset tiene el método for_company, usarlo
            queryset = queryset_base.for_company(company)
        else:
            # Fallback: filtrar manualmente (preserva optimizaciones)
            queryset = queryset_base.filter(company=company)
        
        # Después del filtrado obligatorio por empresa, se pueden aplicar otros filtros
        return queryset
    
    def get_company(self):
        """Retorna la empresa actual del request."""
        if hasattr(self.request, 'current_company'):
            return self.request.current_company
        return None


class CompanyObjectMixin:
    """
    Mixin que verifica que un objeto pertenezca a la empresa actual.
    OBLIGATORIO para DetailView, UpdateView, DeleteView.
    IMPOSIBLE de omitir - siempre obtiene desde queryset filtrado por empresa.
    PRESERVA optimizaciones del queryset (select_related, prefetch_related).
    """
    
    def get_object(self, queryset=None):
        """
        Obtiene el objeto desde un queryset YA FILTRADO por empresa.
        No permite obtener objetos sin verificar pertenencia a empresa.
        PRESERVA optimizaciones del queryset (select_related/prefetch).
        """
        company = self.get_company()
        
        if company is None:
            raise Http404('No tiene una empresa activa.')
        
        # Obtener pk del kwargs
        pk = self.kwargs.get(self.pk_url_kwarg)
        
        if pk is None:
            raise AttributeError(
                "{0} must be called with a pk or slug in the URLconf.".format(
                    self.__class__.__name__
                )
            )
        
        # Si no se pasó queryset, obtenerlo (ya vendrá filtrado por CompanyFilterMixin si se usa)
        if queryset is None:
            queryset = self.get_queryset()
        
        # Filtrar el queryset preservando optimizaciones (select_related/prefetch)
        # NO usar el manager (queryset.model.objects...) para no perder optimizaciones
        if hasattr(queryset, 'for_company'):
            # Si el queryset tiene el método for_company, usarlo
            queryset_filtered = queryset.for_company(company)
        elif hasattr(queryset, 'get_or_404_for_company'):
            # Si tiene get_or_404_for_company, usarlo directamente
            return queryset.get_or_404_for_company(company, pk=pk)
        else:
            # Fallback: filtrar manualmente (preserva optimizaciones del queryset)
            queryset_filtered = queryset.filter(company=company)
        
        # Obtener el objeto desde el queryset filtrado
        try:
            obj = get_object_or_404(queryset_filtered, pk=pk)
        except Http404:
            # Logging: intento de acceso cross-tenant
            logger.warning(
                f'Intento de acceso cross-tenant (404). '
                f'user_id={self.request.user.id}, username={self.request.user.username}, '
                f'company_id={company.id if company else None}, model={self.model.__name__}, '
                f'object_pk={pk}, path={self.request.path}, method={self.request.method}, '
                f'ip={get_client_ip(self.request)}, user_agent={self.request.META.get("HTTP_USER_AGENT", "N/A")[:100]}'
            )
            raise
        
        # Doble verificación por seguridad adicional
        if hasattr(obj, 'company') and obj.company != company:
            # Logging: discrepancia de company detectada
            logger.error(
                f'Discrepancia de company detectada (objeto no pertenece a empresa). '
                f'user_id={self.request.user.id}, username={self.request.user.username}, '
                f'expected_company_id={company.id}, object_company_id={obj.company.id}, '
                f'model={self.model.__name__}, object_pk={pk}, path={self.request.path}, '
                f'method={self.request.method}, ip={get_client_ip(self.request)}'
            )
            raise Http404('El objeto no pertenece a su empresa.')
        
        return obj
    
    def get_company(self):
        """Retorna la empresa actual del request."""
        if hasattr(self.request, 'current_company'):
            return self.request.current_company
        return None
