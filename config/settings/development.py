# config/settings/development.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hamrah_tire_db',
        'USER': 'postgres',
        'PASSWORD': 'test',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Email settings for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
DEFAULT_FROM_EMAIL = 'test@example.com'
FRONTEND_URL = 'http://localhost:3000'  # Update this to match your frontend URL