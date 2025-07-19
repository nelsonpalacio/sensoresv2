from pathlib import Path
import os  # Necesario para STATIC_ROOT y otros paths

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# CLAVE SECRETA (en producción, mejor usar variable de entorno)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-78%1i+x#=fdzw*7j@0vuz&+-!kl6z_q-ibz@p_d+w2jet_k(_9')

# MODO DEBUG (usar False en producción)
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

# HOSTS PERMITIDOS (en producción, definir dominio o IP)
ALLOWED_HOSTS = ['*']

# APLICACIONES INSTALADAS
INSTALLED_APPS = [
    # Apps por defecto de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Tu app
    'sensores_app',
]

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLS Y WSGI
ROOT_URLCONF = 'sensores.urls'
WSGI_APPLICATION = 'sensores.wsgi.application'

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Si usas carpeta global de templates: [BASE_DIR / 'templates']
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

# BASE DE DATOS (sqlite3 para desarrollo; en producción usar otra si quieres)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# VALIDADORES DE CONTRASEÑA
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# LOCALIZACIÓN
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ARCHIVOS ESTÁTICOS
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Si usas carpeta static personalizada en tu app:
# STATICFILES_DIRS = [BASE_DIR / 'static']

# CONFIGURACIÓN POR DEFECTO DE MODELOS
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
