"""
Utilidades de auditoría.
NUNCA se registran contraseñas, datos de tarjetas ni otros campos sensibles.
Toda llave sensible (password, token, secret, key, card, etc.) se reemplaza por [REDACTED].
"""

from core.models import AuditLog


# Claves que NUNCA se guardan: sus valores se reemplazan por [REDACTED] antes de persistir
_SENSITIVE_KEYS = frozenset({
    'password', 'passwd', 'pwd', 'password1', 'password2', 'old_password', 'new_password',
    'secret', 'token', 'key', 'api_key', 'apikey', 'access_token', 'refresh_token',
    'card', 'card_number', 'cardnumber', 'numero_tarjeta', 'cvv', 'cvc', 'security_code',
    'credit_card', 'creditcard', 'card_expiry', 'expiry', 'card_holder',
})


def _is_sensitive_key(key):
    if not isinstance(key, str):
        return False
    k = key.lower().strip()
    if k in _SENSITIVE_KEYS:
        return True
    for sk in _SENSITIVE_KEYS:
        if sk in k or k in sk:
            return True
    return False


def _sanitize_changes(obj):
    """
    Elimina claves sensibles de un dict (o valores anidados).
    No modifica el original; devuelve una copia segura.
    """
    if obj is None:
        return None
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        if _is_sensitive_key(k):
            out[k] = '[REDACTED]'
            continue
        if isinstance(v, dict):
            out[k] = _sanitize_changes(v)
        elif isinstance(v, list):
            out[k] = [_sanitize_changes(item) if isinstance(item, dict) else item for item in v]
        else:
            out[k] = v
    return out


def log_audit(
    company,
    user,
    action,
    model_name,
    object_id=None,
    changes=None,
    ip_address=None
):
    """
    Helper para registrar acciones en el log de auditoría.
    Los campos sensibles (contraseñas, tarjetas, tokens) se redactan y NUNCA se persisten.
    
    Args:
        company: Instancia de Company
        user: Instancia de User o None
        action: Acción realizada ('create', 'update', 'delete', 'view')
        model_name: Nombre del modelo (ej: 'Customer')
        object_id: ID del objeto afectado (opcional)
        changes: Dict con cambios realizados (opcional); se sanitiza antes de guardar
        ip_address: Dirección IP (opcional)
    
    Returns:
        AuditLog: Instancia creada
    """
    if changes is None:
        changes = {}
    changes = _sanitize_changes(changes)
    
    return AuditLog.objects.create(
        company=company,
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        changes=changes,
        ip_address=ip_address
    )

