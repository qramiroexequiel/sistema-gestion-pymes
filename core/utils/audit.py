"""
Utilidades de auditoría.
"""

from core.models import AuditLog


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
    
    Args:
        company: Instancia de Company
        user: Instancia de User o None
        action: Acción realizada ('create', 'update', 'delete', 'view')
        model_name: Nombre del modelo (ej: 'Customer')
        object_id: ID del objeto afectado (opcional)
        changes: Dict con cambios realizados (opcional)
        ip_address: Dirección IP (opcional)
    
    Returns:
        AuditLog: Instancia creada
    """
    if changes is None:
        changes = {}
    
    return AuditLog.objects.create(
        company=company,
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        changes=changes,
        ip_address=ip_address
    )

