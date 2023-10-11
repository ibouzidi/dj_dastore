from .base import *

# RECAPTCHA_PUBLIC_KEY = config('RECAPTCHA_PUBLIC_KEY', cast=str)
# RECAPTCHA_PRIVATE_KEY = config('RECAPTCHA_PRIVATE_KEY', cast=str)

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
        'level': 'DEBUG',
    },
}

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

MIDDLEWARE += [
    'dj_dastore.securityheadersmiddleware.PermissionsPolicyMiddleware',
    'csp.middleware.CSPMiddleware',
]

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

# CSRF & COOKIES

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True

# HSTS 

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin'

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net/npm/chart.js@2.9.3/dist/Chart.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/notyf/3.10.0/notyf.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery-easing/1.4.1/jquery.easing.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/aos/2.3.4/aos.js",
    "https://cdn.jsdelivr.net/npm/chart.js@2.9.3/dist/Chart.min.js",
    "https://www.google.com/recaptcha/api.js",
    "https://www.gstatic.com/recaptcha/",
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
    "https://fonts.googleapis.com",
    "https://js.stripe.com",

)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://appsrv1-147a1.kxcdn.com",
    "https://bootdey.com",
    "https://q.stripe.com",
)
CSP_FONT_SRC = (
    "'self'",
    "https://cdnjs.cloudflare.com",
    "https://fonts.gstatic.com",
    "https://cdnjs.cloudflare.com",
)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_CONNECT_SRC = (
    "'self'",
    "https://api.stripe.com",
    "https://js.stripe.com",
)
CSP_FRAME_SRC = ("'self'",
                 "https://js.stripe.com",
                 "https://hooks.stripe.com",
                 "https://www.google.com",)
CSP_MANIFEST_SRC = ("'self'",)
CSP_MEDIA_SRC = ("'self'",)
CSP_WORKER_SRC = ("'none'",)
CSP_REPORT_URI = "https://64c2850b0d9f1715d85086c4.endpoint.csper.io/?v=2"

# CONFIGURE Storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# DEFAULT_FILE_STORAGE = 'storages.backends.ftp.FTPStorage'
# FTP_STORAGE_LOCATION = config('FTP_STORAGE')


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', cast=str)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', cast=str)
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', cast=str)
EMAIL_PORT = config('EMAIL_PORT', cast=str)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool)

RECAPTCHA_PUBLIC_KEY = config('RECAPTCHA_PUBLIC_KEY', cast=str)
RECAPTCHA_PRIVATE_KEY = config('RECAPTCHA_PRIVATE_KEY', cast=str)

# DEFAULT_FILE_STORAGE = 'storages.backends.ftp.FTPStorage'
# FTP_STORAGE_LOCATION = config('FTP_STORAGE')
