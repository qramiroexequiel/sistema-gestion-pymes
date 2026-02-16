"""
Constantes del sistema.
Definiciones centralizadas de roles y otros valores constantes.
"""

# Constantes de roles
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_OPERATOR = 'operator'
ROLE_VIEWER = 'viewer'

ROLE_CHOICES = [
    (ROLE_ADMIN, 'Administrador'),
    (ROLE_MANAGER, 'Gestor'),
    (ROLE_OPERATOR, 'Operador'),
    (ROLE_VIEWER, 'Visualizador'),
]

