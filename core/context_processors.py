"""
Context processors para templates.
"""


def company(request):
    """Añade la empresa actual al contexto de los templates."""
    return {
        'current_company': getattr(request, 'current_company', None),
        'current_membership': getattr(request, 'current_membership', None),
    }

