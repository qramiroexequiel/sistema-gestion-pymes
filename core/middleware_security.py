"""
Middleware de seguridad: detección de cambio de IP.
Si la IP del usuario cambia respecto a la última guardada en sesión,
registra un AuditLog con SECURITY_ALERT: IP_CHANGE.
Debe ejecutarse después de SessionMiddleware y AuthenticationMiddleware.
"""

import logging
from django.utils.deprecation import MiddlewareMixin

from core.utils.request import get_client_ip
from core.utils.audit import log_audit
from core.models import Company

logger = logging.getLogger('security')

SESSION_KEY_LAST_IP = 'last_known_ip'


class SecurityAlertMiddleware(MiddlewareMixin):
    """
    Verifica la IP del usuario. Si cambia respecto a la última sesión,
    registra SECURITY_ALERT: IP_CHANGE en AuditLog.
    """

    def process_request(self, request):
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return None

        current_ip = get_client_ip(request)
        if not current_ip:
            return None

        last_ip = request.session.get(SESSION_KEY_LAST_IP)
        request.session[SESSION_KEY_LAST_IP] = current_ip

        if last_ip is None:
            return None

        if last_ip == current_ip:
            return None

        company = getattr(request, 'current_company', None)
        if company is None:
            company_id = request.session.get('current_company_id')
            if company_id:
                try:
                    company = Company.objects.get(pk=company_id, active=True)
                except Company.DoesNotExist:
                    pass
        if company is None:
            return None

        try:
            log_audit(
                company=company,
                user=request.user,
                action='security_alert',
                model_name='SecurityAlert',
                object_id=None,
                changes={
                    'alert_type': 'IP_CHANGE',
                    'from_ip': last_ip,
                    'to_ip': current_ip,
                },
                ip_address=current_ip,
            )
            logger.warning(
                f'SECURITY_ALERT: IP_CHANGE user_id={request.user.id} '
                f'from={last_ip} to={current_ip}'
            )
        except Exception as e:
            logger.exception('Error registrando alerta IP_CHANGE: %s', e)

        return None
