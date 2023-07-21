from pathlib import Path
from decouple import Csv, config
import os
from django.contrib.messages import constants as messages
from django.core.management.utils import get_random_secret_key


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default=get_random_secret_key())

print("SECRET_KEY")
print(SECRET_KEY)
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
    'team.apps.TeamConfig',
    'log.apps.LogConfig',
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


DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760 # 10mb = 10 * 1024 *1024


JAZZMIN_SETTINGS = {
    "welcome_sign": "Welcome to Admin Panel.",
    "site_title": "Admin Panel",
    "site_header": "Panel",
    "site_logo": "dastore/logo_dastore_no_text.png",
    "site_logo_classes": ".logo-panel",
    "copyright": "DaStore",

}

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

SESSION_COOKIE_AGE = 86400  # 24 hours

LOGIN_URL = 'two_factor:login'

LOGIN_REDIRECT_URL = 'account:account_profile'


RECAPTCHA_PUBLIC_KEY = '6LdEG1smAAAAAAEn-_8vrhE4eUeVgMKhiW8Tr_eP'
RECAPTCHA_PRIVATE_KEY = '6LdEG1smAAAAAFNBtdDqDaUJrFWknkdtz-fETWIB'
# SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# Stripe And Dj-stripe config
STRIPE_TEST_PUBLIC_KEY = config('STRIPE_TEST_PUBLIC_KEY', cast=str)
STRIPE_TEST_SECRET_KEY = config('STRIPE_TEST_SECRET_KEY', cast=str)
STRIPE_LIVE_MODE = config('STRIPE_LIVE_MODE', cast=bool)
DJSTRIPE_WEBHOOK_SECRET = config('DJSTRIPE_WEBHOOK_SECRET', cast=str)

DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
DJSTRIPE_USE_NATIVE_JSONFIELD = True

# stripe listen --forward-to localhost:8000/stripe/webhook/
# python manage.py djstripe_sync_models
# python manage.py djstripe_sync_plans_from_stripe

# LOAD Fixtures
# python manage.py loaddata <fixturename>
