from pathlib import Path
from decouple import Csv, config
import os
from django.contrib.messages import constants as messages


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY",
                    default="django-insecure$dj_dastore.settings.local")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost",
                       cast=Csv())

# =====================================================================
# APPLICATIONS DEFINITION
# =====================================================================

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'account.apps.AccountConfig',
    'app.apps.AppConfig',
    'extbackup.apps.ExtbackupConfig',
    'folder.apps.FolderConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'storages',
    'widget_tweaks',
    'bootstrap_modal_forms',
    # 2fa Authentication
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'two_factor',
    # Recaptcha
    'captcha',

    'djstripe',
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

WSGI_APPLICATION = 'dj_dastore.wsgi.application'

ROOT_URLCONF = 'dj_dastore.urls'

# =====================================================================
# MIDDLEWARE SETTINGS
# =====================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'dj_dastore.redirect_middleware.HtmxRedirectMiddleware',
]

# =====================================================================
# TEMPLATES SETTINGS
# =====================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'templates'],
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

# =====================================================================
# DATABASES SETTINGS
# =====================================================================

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

# =====================================================================
# AUTHENTICATION BACKENDS SETTINGS
# =====================================================================

AUTH_USER_MODEL = 'account.Account' #

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'account.backends.CaseInsensitiveModelBackend',
]

# =====================================================================
# AUTHENTICATION AND AUTHORIZATION SETTINGS
# =====================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': f'django.contrib.auth.password_validation.UserAttribute'
                f'SimilarityValidator',
    },
    {
        'NAME': f'django.contrib.auth.password_validation.MinimumLength'
                f'Validator',
    },
    {
        'NAME': f'django.contrib.auth.password_validation.CommonPassword'
                f'Validator',
    },
    {
        'NAME': f'django.contrib.auth.password_validation.NumericPassword'
                f'Validator',
    },
]

# =====================================================================
# INTERNATIONALIZATION AND LOCALIZATION SETTINGS
# =====================================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = False

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

BASE_URL = "http://127.0.0.1:8000"

# =====================================================================
# THIRD-PARTY SETTINGS SETTINGS
# =====================================================================


MESSAGE_TAGS = {
    messages.DEBUG:     'alert-info',
    messages.INFO:      'alert-info',
    messages.SUCCESS:   'alert-success',
    messages.WARNING:   'alert-warning',
    messages.ERROR:     'alert-danger',
}

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # During development only

DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760 # 10mb = 10 * 1024 *1024

# CONFIGURE FTP
# DEFAULT_FILE_STORAGE = 'storages.backends.ftp.FTPStorage'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# FTP_STORAGE_LOCATION = 'ftp://test:test@localhost:21/'


JAZZMIN_SETTINGS = {
    "welcome_sign": "Welcome to Admin Panel.",
    "site_title": "Admin Panel",
    "site_header": "Panel",
    "site_logo": "dastore/logo_dastore_no_text.png",
    "site_logo_classes": ".logo-panel",
    "copyright": "DaStore",

}

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

LOGIN_URL = 'two_factor:login'

LOGIN_REDIRECT_URL = 'account:account_profile'


RECAPTCHA_PUBLIC_KEY = '6LdEG1smAAAAAAEn-_8vrhE4eUeVgMKhiW8Tr_eP'
RECAPTCHA_PRIVATE_KEY = '6LdEG1smAAAAAFNBtdDqDaUJrFWknkdtz-fETWIB'
# SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# stripe config
STRIPE_TEST_PUBLIC_KEY = 'pk_test_51Han4nJWztZpQABxysTVGo4JzUVAofIK57O8wrZgN0vvjBsbQYja5RdeMdOKyGaaZUK9OdbmjJF9xUp6RVyrTYz200ofLajlDL'
STRIPE_TEST_SECRET_KEY = 'sk_test_51Han4nJWztZpQABxCCz5MlmSTiTzZIVFuFjgsSAfy0iLWQ1TQ2rNi5yYtdtQuiM0DfaxIYeXNJL2ZmmQAwaOHXzs0017w3y1IW'
STRIPE_LIVE_MODE = False

# Dj-stripe config
DJSTRIPE_WEBHOOK_SECRET = 'whsec_56d7c095da9b777a89840d2b4ec445f19c4a5c42e51d73566a857b545d87b4c4'
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
DJSTRIPE_USE_NATIVE_JSONFIELD = True

#stripe listen --forward-to localhost:8000/stripe/webhook/
