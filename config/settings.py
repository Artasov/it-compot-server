import os
from datetime import timedelta
from pathlib import Path

# Environment helper
env = os.environ.get

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / 'data'

# Basic settings
DEBUG = bool(int(env('DEBUG', 0)))
DEV = bool(int(env('DEV', 0)))
SECRET_KEY = env('SECRET_KEY', 'your-secret-key')
ALLOWED_HOSTS = ['localhost', env('MAIN_DOMAIN', '127.0.0.1')] + env('ALLOWED_HOSTS', '').split(',')
ROOT_URLCONF = 'Core.urls'

# Security and domain settings
HTTPS = bool(int(env('HTTPS', 0)))
MAIN_DOMAIN = env('MAIN_DOMAIN', '127.0.0.1')

# Database and cache
REDIS_BASE_URL = 'redis://127.0.0.1:6379/'
REDIS_URL = env('REDIS_URL', REDIS_BASE_URL + '0')
REDIS_CACHE_URL = env('REDIS_CACHE_URL', REDIS_BASE_URL + '1')
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
DJANGO_REDIS_LOGGER = 'RedisLogger'

# Static and media files
STATIC_URL = f'http{"s" if HTTPS else ""}://{MAIN_DOMAIN}/static/'
MEDIA_URL = f'http{"s" if HTTPS else ""}://{MAIN_DOMAIN}/media/'
STATIC_ROOT = BASE_DIR.parent / 'static'
MEDIA_ROOT = BASE_DIR.parent / 'media'
STATICFILES_DIRS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Additional settings
SERVICE_ROOT = BASE_DIR / 'service'
DEVELOPER_EMAIL = 'ivanhvalevskey@gmail.com'
HOLLIHOP_DOMAIN = 'it-school.t8s.ru'
HOLLIHOP_AUTHKEY = env('AUTHKEY')
TEACHER_SALARY_PASSWORD = env('TEACHER_SALARY_PASSWORD')
GOOGLE_API_JSON_CREDS_PATH = BASE_DIR / 'it-compot-web-client_creds.json'
TABLE_TEACHERS_SALARY = ('1T5Np2RdqBCdmo7IUm9FGBG6mZWY138arUWPJOBs-slY', '690189137')

# Django settings
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Core',
    'tools',
]

DATABASES = {
    'default': {
        'ENGINE': env('SQL_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': env('SQL_DATABASE_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': env('SQL_USER', 'admin'),
        'PASSWORD': env('SQL_PASSWORD', 'admin'),
        'HOST': env('SQL_HOST', 'localhost'),
        'PORT': env('SQL_PORT', '5432'),
    }
}

CACHES = {
    'default': {
        "BACKEND": "django_redis.cache.RedisCache",
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'base_formatter': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
            'encoding': 'utf-8',
        }
    },
    'handlers': {
        # 'file': {
        #     'level': 'DEBUG',
        #     'class': 'logging.FileHandler',
        #     'filename': BASE_DIR / 'django.log',
        #     'formatter': 'base_formatter',
        #     'encoding': 'utf-8',
        # },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'base_formatter',
        },
    },
    'loggers': {
        'Core': {
            'handlers': ['console'],  # ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # 'app_name': {
        #     'handlers':...
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

if DEV:
    import mimetypes

    mimetypes.add_type("application/javascript", ".js", True)
    INTERNAL_IPS = ('127.0.0.1',)
    MIDDLEWARE += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    INSTALLED_APPS += (
        'debug_toolbar',
    )
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]

    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
