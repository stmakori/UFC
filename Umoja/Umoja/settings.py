import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='your_django_secret_key_here')

# Security
DEBUG = config('DEBUG', default=True, cast=bool)

# Payhero Configuration
PAYHERO_API_KEY = config('PAYHERO_API_KEY')
PAYHERO_SECRET_KEY = config('PAYHERO_SECRET_KEY')
PAYHERO_ACCOUNT_ID = config('PAYHERO_ACCOUNT_ID', default='3425')
PAYHERO_BASIC_AUTH_TOKEN = config('PAYHERO_BASIC_AUTH_TOKEN')
PAYHERO_BASE_URL = config('PAYHERO_BASE_URL', default='https://backend.payhero.co.ke')
PAYHERO_CHANNEL_ID = config('PAYHERO_CHANNEL_ID', default='4630')
PAYHERO_WEBHOOK_SECRET = config('PAYHERO_WEBHOOK_SECRET', default='your_actual_webhook_secret')

# Login/Logout URLs
LOGIN_URL = config('LOGIN_URL', default='/login/')
LOGIN_REDIRECT_URL = config('LOGIN_REDIRECT_URL', default='/dashboard/')
LOGOUT_REDIRECT_URL = config('LOGOUT_REDIRECT_URL', default='/')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'umoja',
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

ROOT_URLCONF = 'Umoja.urls'

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

WSGI_APPLICATION = 'Umoja.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Payhero Configuration - Using python-decouple (lines 13-19 above)
# The settings above (lines 13-19) use config() from python-decouple
# Remove the duplicate settings below if not needed
# PAYHERO_API_KEY = os.environ.get('PAYHERO_API_KEY', 'your_payhero_api_key_here')
# PAYHERO_SECRET_KEY = os.environ.get('PAYHERO_SECRET_KEY', 'your_payhero_secret_key_here')
# PAYHERO_BASE_URL = os.environ.get('PAYHERO_BASE_URL', 'https://api.payhero.com')
# PAYHERO_WEBHOOK_SECRET = os.environ.get('PAYHERO_WEBHOOK_SECRET', 'your_webhook_secret_here')