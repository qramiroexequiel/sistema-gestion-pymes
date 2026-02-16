"""
Utilidades relacionadas con requests HTTP.
"""


def get_client_ip(request):
    """
    Obtiene la IP del cliente desde request.
    
    Args:
        request: HttpRequest de Django
    
    Returns:
        str: Dirección IP del cliente
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

