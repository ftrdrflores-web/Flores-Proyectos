"""
Django settings for backend_project project.
"""

from pathlib import Path
from datetime import timedelta
import os
import environ
from dotenv import load_dotenv

# ===== Inicializar lectura de environ =====
env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Leer el archivo .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
load_dotenv()

# ===== Seguridad =====
SECRET_KEY = env('SECRET_KEY', default='django-insecure-viu&&%m5p%xfxg1m26x)4)6r^0x!3nkx8rkf*q9&zxieu5z(g(')
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


# ===== Aplicaciones =====
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_apscheduler',
    # Apps del proyecto
    'core_data',
    'users',
    'players',
    'wars',
    'stats',
]

# ===== Middleware =====
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',           # CORS - debe ir antes de CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend_project.wsgi.application'


# ===== Base de datos =====
DATABASES = {
    'default': env.db()
}


# ===== Validación de contraseñas =====
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ===== Internacionalización =====
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Tijuana'
USE_I18N = True
USE_TZ = True


# ===== Archivos estáticos =====
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ===== Encriptación de datos sensibles =====
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY').encode()


# ===== Django REST Framework =====
REST_FRAMEWORK = {
    # Autenticación por defecto: JWT
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Por defecto todos los endpoints requieren autenticación
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Paginación global
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Formato de respuesta
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    # Throttling (límite de requests)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}


# ===== JWT Configuración =====
SIMPLE_JWT = {
    # Access token válido por 1 día
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    # Refresh token válido por 30 días
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    # Rotar refresh token en cada uso (más seguro)
    'ROTATE_REFRESH_TOKENS': True,
    # Invalidar el refresh token anterior al rotar
    'BLACKLIST_AFTER_ROTATION': True,
    # Actualizar last_login al hacer login
    'UPDATE_LAST_LOGIN': True,
    # Algoritmo de firma
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    # Headers
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    # Claims del token
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    # Tipo de token
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


# ===== CORS (para React en desarrollo) =====
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',    # React dev server
    'http://127.0.0.1:3000',
    'http://localhost:5173',    # Vite dev server (por si usamos Vite)
    'http://127.0.0.1:5173',
]

# En desarrollo, permitir cookies
CORS_ALLOW_CREDENTIALS = True

# Headers permitidos
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]