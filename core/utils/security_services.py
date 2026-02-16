"""
Servicios de detección de anomalías y alertas de seguridad.
"""

from django.utils import timezone
from datetime import timedelta

from core.models import AuditLog
from core.utils.audit import log_audit


def check_anomalous_behavior(user, company):
    """
    Revisa los AuditLog de los últimos 10 minutos del usuario en la empresa.
    Si hay más de 3 acciones de tipo DELETE o cancelaciones de operaciones,
    registra SECURITY_ALERT: MASS_DELETION.
    """
    cutoff = timezone.now() - timedelta(minutes=10)
    logs = AuditLog.objects.filter(
        company=company,
        user=user,
        timestamp__gte=cutoff,
    ).order_by('-timestamp')

    count = 0
    for log in logs:
        if log.action == 'delete':
            count += 1
        elif (
            log.action in ('update', 'cancel')
            and log.model_name == 'Operation'
            and isinstance(log.changes, dict)
            and log.changes.get('status') == 'cancelled'
        ):
            count += 1
        if count > 3:
            break

    if count > 3:
        log_audit(
            company=company,
            user=user,
            action='security_alert',
            model_name='SecurityAlert',
            object_id=None,
            changes={
                'alert_type': 'MASS_DELETION',
                'count': count,
                'window_minutes': 10,
            },
            ip_address=None,
        )
        return True
    return False
