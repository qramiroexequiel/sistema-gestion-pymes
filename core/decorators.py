"""
Decoradores para funciones de vista que requieren acceso a empresa.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def company_required(view_func):
    """Decorador que requiere que el usuario tenga una empresa asociada."""
    
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'current_company') or not request.current_company:
            from django.contrib import messages
            messages.error(request, 'Debe seleccionar una empresa para continuar.')
            return redirect('core:company_select')
        return view_func(request, *args, **kwargs)
    
    return wrapper


def role_required(*roles):
    """Decorador que requiere un rol específico en la empresa actual."""
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'current_membership') or not request.current_membership:
                raise PermissionDenied('No tiene una membresía activa en esta empresa.')
            
            if roles and request.current_membership.role not in roles:
                raise PermissionDenied(f'Se requiere uno de los siguientes roles: {", ".join(roles)}')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

