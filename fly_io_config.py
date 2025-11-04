# Fly.io Configuration for PublicBridge
# This file contains settings specific to Fly.io deployment

import os

# Fly.io specific settings
DEBUG = False
ALLOWED_HOSTS = ['*']  # Fly.io will handle this via fly.toml

# Static files configuration for Fly.io
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'

# Media files configuration for Fly.io
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Database configuration (Fly.io provides PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'publicbridge'),
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Whitenoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Fly.io specific optimizations
USE_TZ = True
TIME_ZONE = 'UTC'

# Logging configuration for Fly.io
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}