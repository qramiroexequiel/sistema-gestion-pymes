"""
Django base settings for Pymes Management System.

Configuración base compartida entre todos los entornos.
Variables sensibles se cargan desde .env (python-dotenv).
"""

import os
from pathlib import Path

# Cargar .env desde la raíz del proyecto (antes de leer config)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
_env_path = BASE_DIR / '.env'
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass

try:
    from decouple import config, Csv
except ImportError:
    def config(key, default=None, cast=None):
        value = os.getenv(key, default)
        if cast and value is not None:
            return cast(value)
        return value
    def Csv(*args, **kwargs):
        return lambda v: [s.strip() for s in v.split(',')]

# SECRET_KEY: desde .env. En producción NUNCA usar default.
SECRET_KEY = os.getenv('SECRET_KEY') or config(
    'SECRET_KEY',
    default='django-insecure-8sn)j8lrk5$6e2m23=o_+ut06!=b%n@rq9givq%d3=4p%)+20c'
)

# DEBUG: desde .env (default False por seguridad)
_debug_val = (os.getenv('DEBUG') or config('DEBUG', default='False')).strip().lower()
DEBUG = _debug_val in ('true', '1', 'yes')

# URL del admin: desde .env (ej. ADMIN_URL=panel-secreto para ofuscar)
ADMIN_URL = (os.getenv('ADMIN_URL') or config('ADMIN_URL', default='admin/')).strip('/') + '/'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps
    'core',
    'customers',
    'suppliers',
    'products',
    'operations',
    'reports',
    'config_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.CompanyMiddleware',  # Multi-tenant middleware
    'core.middleware_security.SecurityAlertMiddleware',  # Detección cambio IP
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.company',  # Context processor para empresa actual
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Login settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True

# Security headers (siempre activos; producción añade SSL/HSTS)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# Cookies: HTTPONLY para evitar acceso desde JS (XSS)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
# SSL redirect solo en producción (SECURE_SSL_REDIRECT = True en production.py)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Error pages
ADMINS = [
    # ('Admin Name', 'admin@example.com'),
]

# Handler para errores 404 y 500
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Logging configuration base
# Se extiende en development.py y production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'security': {
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
