import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Credenciales locales: .env está ignorado por Git. Las variables del servidor
# tienen prioridad sobre el archivo local.
load_dotenv(BASE_DIR / '.env')

DEBUG = os.getenv('DEBUG', 'False').strip().lower() in {'1', 'true', 'yes', 'on'}

SECRET_KEY = os.getenv('SECRET_KEY', '').strip()
if not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY debe definirse en .env o en las variables del servidor.')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]
if DEBUG and 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')
if not DEBUG and not os.getenv('ALLOWED_HOSTS'):
    raise ImproperlyConfigured('ALLOWED_HOSTS debe definirse cuando DEBUG=False.')

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.diccionario',
    'apps.usuarios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'diccionario_kichwa.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'diccionario_kichwa.wsgi.application'

DATABASE_ENGINE = os.getenv('DATABASE_ENGINE', 'sqlite3').strip().lower()
if DATABASE_ENGINE in {'sqlite', 'sqlite3', 'django.db.backends.sqlite3'}:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            # La ruta SQLite se mantiene separada de DATABASE_NAME, que identifica
            # la base PostgreSQL durante una migración entre motores.
            'NAME': os.getenv('SQLITE_DATABASE_PATH') or BASE_DIR / 'db.sqlite3',
        }
    }
elif DATABASE_ENGINE in {'postgres', 'postgresql', 'django.db.backends.postgresql'}:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DATABASE_NAME', 'diccionario_kichwa'),
            'USER': os.getenv('DATABASE_USER', 'postgres'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
            'HOST': os.getenv('DATABASE_HOST', '127.0.0.1'),
            'PORT': os.getenv('DATABASE_PORT', '5432'),
            'CONN_MAX_AGE': int(os.getenv('DATABASE_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
        }
    }
else:
    raise ImproperlyConfigured(
        'DATABASE_ENGINE debe ser sqlite3 o postgresql. '
        f'Recibido: {DATABASE_ENGINE!r}.'
    )

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'diccionario:home'
LOGOUT_REDIRECT_URL = 'diccionario:home'
PASSWORD_RESET_TIMEOUT = int(os.getenv('PASSWORD_RESET_TIMEOUT', '86400'))

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
    if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').strip().lower() in {'1', 'true', 'yes', 'on'}
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@localhost')

# IA desactivada por defecto; la clave solo existe en el servidor.
KICHWA_AI_PROVIDER = os.getenv('KICHWA_AI_PROVIDER', 'none').strip().lower()
KICHWA_AI_BASE_URL = os.getenv('KICHWA_AI_BASE_URL', '').strip()
KICHWA_AI_API_KEY = os.getenv('KICHWA_AI_API_KEY', '')
KICHWA_AI_MODEL = os.getenv('KICHWA_AI_MODEL', '').strip()
KICHWA_AI_TIMEOUT = int(os.getenv('KICHWA_AI_TIMEOUT', '15'))

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'
    if os.getenv('USE_X_FORWARDED_PROTO', '').strip().lower() in {'1', 'true', 'yes', 'on'}:
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
