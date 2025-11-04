# PythonAnywhere Configuration for PublicBridge
# This file contains settings specific to PythonAnywhere deployment

import os

# PythonAnywhere specific settings
DEBUG = False
ALLOWED_HOSTS = ['*']  # PythonAnywhere will handle this

# Static files configuration for PythonAnywhere
STATIC_URL = '/static/'
STATIC_ROOT = '/home/your-username/publicbridge/static'

# Media files configuration for PythonAnywhere
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/your-username/publicbridge/media'

# Database configuration (PythonAnywhere provides MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'your-username$publicbridge',
        'USER': 'your-username',
        'PASSWORD': 'your-mysql-password',
        'HOST': 'your-username.mysql.pythonanywhere-services.com',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
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