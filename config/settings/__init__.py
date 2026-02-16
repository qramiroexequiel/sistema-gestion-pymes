"""
Settings package for Pymes Management System.
Importa la configuración según el entorno.
"""

import os

# Obtener el entorno desde variable de entorno, por defecto 'development'
ENVIRONMENT = os.getenv('DJANGO_ENV', 'development')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .development import *

