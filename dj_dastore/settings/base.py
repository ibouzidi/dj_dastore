from pathlib import Path
from decouple import Csv, config
import os
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG:     'alert-info',
    messages.INFO:      'alert-info',
    messages.SUCCESS:   'alert-success',
    messages.WARNING:   'alert-warning',
    messages.ERROR:     'alert-danger',
}

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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =====================================================================
# TEMPLATES SETTINGS
# =====================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
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

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.parent / 'static'

# STATICFILES_DIRS = (os.path.join(BASE_DIR, 'accounts/static/'),)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR.parent / 'media/'

# =====================================================================
# THIRD-PARTY SETTINGS SETTINGS
# =====================================================================


