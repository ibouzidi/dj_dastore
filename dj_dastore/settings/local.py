from .base import *

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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CONFIGURE Storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'


# INSTALLED_APPS += ["debug_toolbar"]
#
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
