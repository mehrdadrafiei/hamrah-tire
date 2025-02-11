# config/settings/development.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# This is important for serving static files in development
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

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
DEFAULT_FROM_EMAIL = 'noreply@hamrahtire.com'
FRONTEND_URL = 'http://localhost:8000'  # Change this based on your setup
