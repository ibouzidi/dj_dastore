from .base import *


# ==============================================================================
# DATABASE SETTINGS
# ==============================================================================

DATABASES = {
    "default": {
        "ENGINE": config("SQL_ENGINE", "django.db.backends.postgresql"),
        "NAME": config("SQL_DATABASE"),
        "USER": config("SQL_USER"),
        "PASSWORD": config("SQL_PASSWORD"),
        "HOST": config("SQL_HOST"),
        "PORT": config("SQL_PORT"),
    }
}


# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

# CSRF_COOKIE_SECURE = True
# CSRF_COOKIE_HTTPONLY = True
#
# SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
#
# SESSION_COOKIE_SECURE = True


DEFAULT_FILE_STORAGE = 'storages.backends.ftp.FTPStorage'
FTP_STORAGE_LOCATION = config('FTP_STORAGE')


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST = config('EMAIL_HOST', cast=str)
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str)
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str)
