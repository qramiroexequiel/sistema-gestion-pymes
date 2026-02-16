"""
Middleware para sistema multi-tenant.
Identifica y asocia automáticamente la empresa del usuario autenticado.
GARANTIZA que request.current_company siempre sea válida o None.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from core.models import Membership, Company
from core.utils.request import get_client_ip

logger = logging.getLogger('security')


# Rutas que no requieren empresa activa
PUBLIC_PATHS = [
    '/login/',
    '/logout/',
    '/empresa/seleccionar/',  # URL de selección de empresa
    '/static/',
    '/media/',
    '/favicon.ico',
    '/admin/',  # Admin completo - verificado después si es superuser
]


class CompanyMiddleware(MiddlewareMixin):
    """
    Middleware que identifica la empresa del usuario autenticado
    y la almacena en request.current_company.
    Valida que el usuario tenga Membership activa en la empresa seleccionada.
    """
    
    def process_request(self, request):
        """Procesa la request y asocia la empresa del usuario."""
        request.current_company = None
        request.current_membership = None
        
        # Rutas públicas no requieren empresa (static/media/ico)
        if any(request.path.startswith(path) for path in ['/static/', '/media/', '/favicon.ico']):
            return None
        
        # Admin: si es superuser, no requiere empresa
        if request.path.startswith('/admin/'):
            if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
                return None
            # Para usuarios no-superuser en admin, requerir empresa (como cualquier otra ruta)
        
        # Rutas de login/logout y selección de empresa
        if any(request.path.startswith(path) for path in ['/login/', '/logout/', '/empresa/seleccionar/']):
            return None
        
        # Verificar si es ruta protegida que requiere empresa
        is_protected_path = not any(request.path.startswith(path) for path in PUBLIC_PATHS)
        
        # Solo procesar si el usuario está autenticado
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Intentar obtener la empresa desde la sesión
            company_id = request.session.get('current_company_id')
            
            if company_id:
                try:
                    # Verificar que la membresía existe y está activa
                    membership = Membership.objects.select_related('company').get(
                        user=request.user,
                        company_id=company_id,
                        active=True,
                        company__active=True  # También verificar que la empresa esté activa
                    )
                    request.current_company = membership.company
                    request.current_membership = membership
                except Membership.DoesNotExist:
                    # Si la membresía no existe o no está activa, limpiar sesión
                    if 'current_company_id' in request.session:
                        del request.session['current_company_id']
                    
                    # Logging: intento de acceso con empresa sin membresía válida
                    logger.warning(
                        f'Intento de acceso sin membresía válida. '
                        f'user_id={request.user.id}, username={request.user.username}, '
                        f'company_id={company_id}, path={request.path}, method={request.method}, '
                        f'ip={get_client_ip(request)}, user_agent={request.META.get("HTTP_USER_AGENT", "N/A")[:100]}'
                    )
                    
                    # Buscar la primera membresía activa disponible
                    membership = Membership.objects.select_related('company').filter(
                        user=request.user,
                        active=True,
                        company__active=True
                    ).first()
                    
                    if membership:
                        request.current_company = membership.company
                        request.current_membership = membership
                        request.session['current_company_id'] = membership.company.id
                        logger.info(
                            f'Empresa auto-seleccionada después de membresía inválida. '
                            f'user_id={request.user.id}, company_id={membership.company.id}'
                        )
                    else:
                        # Usuario sin empresas activas
                        logger.warning(
                            f'Usuario sin empresas activas. '
                            f'user_id={request.user.id}, username={request.user.username}, '
                            f'path={request.path}, method={request.method}, '
                            f'ip={get_client_ip(request)}'
                        )
            else:
                # Si no hay empresa en sesión, buscar la primera membresía activa
                membership = Membership.objects.select_related('company').filter(
                    user=request.user,
                    active=True,
                    company__active=True
                ).first()
                
                if membership:
                    request.current_company = membership.company
                    request.current_membership = membership
                    request.session['current_company_id'] = membership.company.id
                else:
                    # Usuario autenticado sin empresas activas
                    logger.warning(
                        f'Usuario autenticado sin empresas activas. '
                        f'user_id={request.user.id}, username={request.user.username}, '
                        f'path={request.path}, method={request.method}, '
                        f'ip={get_client_ip(request)}'
                    )
        elif is_protected_path:
            # Ruta protegida sin autenticación (será manejado por LoginRequiredMixin)
            # No loguear aquí para evitar ruido, ya que es comportamiento esperado
            pass
        
        # Logging: ruta protegida sin empresa activa
        if (is_protected_path and 
            hasattr(request, 'user') and 
            request.user.is_authenticated and 
            (not hasattr(request, 'current_company') or not request.current_company)):
            logger.warning(
                f'Ruta protegida sin empresa activa. '
                f'user_id={request.user.id}, username={request.user.username}, '
                f'path={request.path}, method={request.method}, '
                f'ip={get_client_ip(request)}, user_agent={request.META.get("HTTP_USER_AGENT", "N/A")[:100]}'
            )
        
        return None

