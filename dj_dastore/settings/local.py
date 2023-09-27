from .base import *

# =====================================================================
# STATIC FILES AND MEDIA FILES SETTINGS
# =====================================================================

STATICFILES_DIRS = [
    BASE_DIR.parent / 'static',
    BASE_DIR.parent / 'media',
]
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR.parent / 'static_cdn'
MEDIA_ROOT = BASE_DIR.parent / 'media_cdn'

TEMP = BASE_DIR.parent / 'media_cdn/temp'

# ==============================================================================
# DATABASE SETTINGS
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': '3306',
        'OPTIONS': {
            'charset': config('DB_CHARSET')
        }
    }
}

# During development only
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CONFIGURE Storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# INSTALLED_APPS += ["debug_toolbar"]
#
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST', cast=str)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str)
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str)
# EMAIL_PORT = config('EMAIL_PORT', cast=str)
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
# EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool)
