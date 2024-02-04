import os
from datetime import timedelta
from pathlib import Path

import environ
from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / 'data'

# Environment helper
env = os.environ.get
DEV = bool(int(env('DEV', 0)))
if not DEV:
    dotenv_path = os.path.join(BASE_DIR, '.env.prod')
    load_dotenv(dotenv_path=dotenv_path)

# Basic settings
DEBUG = bool(int(env('DEBUG', 0)))
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
if DEV:
    STATIC_URL = f'http{"s" if HTTPS else ""}://{MAIN_DOMAIN}/static/' if not DEV else '/static/'
    MEDIA_URL = f'http{"s" if HTTPS else ""}://{MAIN_DOMAIN}/media/' if not DEV else '/media/'
    STATIC_ROOT = BASE_DIR.parent / 'static'
    MEDIA_ROOT = BASE_DIR.parent / 'media'
else:
    MINIO_ENDPOINT = 'minio:9000'
    MINIO_EXTERNAL_ENDPOINT = f'{MAIN_DOMAIN}:9000'  # For external access use Docker hostname and MinIO port
    MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = bool(int(env('MINIO_EXTERNAL_ENDPOINT_USE_HTTPS') or 0))
    MINIO_ACCESS_KEY = env('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = env('MINIO_SECRET_KEY')
    MINIO_USE_HTTPS = bool(int(env('MINIO_USE_HTTPS') or 0))
    MINIO_URL_EXPIRY_HOURS = timedelta(days=1)
    MINIO_CONSISTENCY_CHECK_ON_START = True
    MINIO_PRIVATE_BUCKETS = [
        'django-backend-dev-private',
    ]
    MINIO_PUBLIC_BUCKETS = [
        'django-backend-dev-public',
    ]
    MINIO_POLICY_HOOKS: list[tuple[str, dict]] = []
    MINIO_MEDIA_FILES_BUCKET = 'media'  # Just bucket name may be 'media-files'?
    MINIO_STATIC_FILES_BUCKET = 'static'  # Just bucket name may be 'my-static-files'?
    MINIO_BUCKET_CHECK_ON_SAVE = True  # Default: True // Creates a cart if it doesn't exist, then saves it
    DEFAULT_FILE_STORAGE = 'django_minio_backend.models.MinioBackend'
    MINIO_PUBLIC_BUCKETS.append(MINIO_STATIC_FILES_BUCKET)
    MINIO_PUBLIC_BUCKETS.append(MINIO_MEDIA_FILES_BUCKET)
    MINIO_PUBLIC_BUCKETS.append('files-bucket')

    STATICFILES_STORAGE = 'django_minio_backend.models.MinioBackendStatic'
    FILE_UPLOAD_MAX_MEMORY_SIZE = 65536

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TZ', 'Europe/Moscow')
USE_I18N = True
USE_TZ = True

# Additional settings
SERVICE_ROOT = BASE_DIR / 'service'
DEVELOPER_EMAIL = 'ivanhvalevskey@gmail.com'
HOLLIHOP_DOMAIN = env('HOLLIHOP_DOMAIN')
HOLLIHOP_AUTHKEY = env('HOLLIHOP_AUTHKEY')
TEACHER_SALARY_PASSWORD = env('TEACHER_SALARY_PASSWORD')

# Google Sheets
GOOGLE_API_JSON_CREDS_PATH = BASE_DIR / env('GSCREDS_FILE_NAME', '')
GSDOCID_LOG_JOIN_FORMING_GROUPS = env('GSDOCID_LOG_JOIN_FORMING_GROUPS', '')
GSDOCID_TEACHERS_SALARY = env('GSDOCID_TEACHERS_SALARY', '')
TABLE_TEACHERS_SALARY = (GSDOCID_TEACHERS_SALARY, '690189137')

# Django settings
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'adrf',
    'channels',

    'Core',
    'tools',
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': env('SQL_ENGINE', 'django.db.backends.sqlite3') if not DEV else 'django.db.backends.sqlite3',
#         'NAME': env('SQL_DATABASE_NAME', BASE_DIR / 'db.sqlite3') if not DEV else BASE_DIR / 'db.sqlite3',
#         'USER': env('SQL_USER', 'admin') if not DEV else 'admin',
#         'PASSWORD': env('SQL_PASSWORD', 'admin') if not DEV else 'admin',
#         'HOST': env('SQL_HOST', 'localhost') if not DEV else 'localhost',
#         'PORT': env('SQL_PORT', '5432') if not DEV else '5432',
#     }
# }
if not DEV:
    CACHES = {
        'default': {
            "BACKEND": "django_redis.cache.RedisCache",
            'LOCATION': REDIS_CACHE_URL,
            'OPTIONS': {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            # "hosts": [('redis', 6379)],
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Logging
logs_prod_dir = os.path.join(BASE_DIR, 'logs/django_prod')
logs_dev_dir = os.path.join(BASE_DIR, 'logs/django_dev')
logs_sql_prod_dir = os.path.join(BASE_DIR, 'logs/django_prod/sql')
logs_sql_dev_dir = os.path.join(BASE_DIR, 'logs/django_dev/sql')

for path in [logs_prod_dir, logs_dev_dir, logs_sql_prod_dir, logs_sql_dev_dir]:
    os.makedirs(path, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'base_formatter': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        }
    },
    'handlers': {
        'file_sql': {
            'level': 'DEBUG' if DEBUG and DEV else 'WARNING',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(logs_sql_dev_dir if DEBUG and DEV else logs_sql_prod_dir, 'sql.log'),
            'when': 'midnight',
            'backupCount': 30,  # How many days to keep logs
            'formatter': 'base_formatter',
            'encoding': 'utf-8',
        },
        'file': {
            'level': 'DEBUG' if DEBUG and DEV else 'WARNING',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(logs_dev_dir if DEBUG and DEV else logs_prod_dir, 'django.log'),
            'when': 'midnight',
            'backupCount': 30,  # How many days to keep logs
            'formatter': 'base_formatter',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'DEBUG' if DEBUG and DEV else 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'base_formatter',
        },
    },
    'loggers': {
        'base': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG and DEV else 'WARNING',
            'propagate': True,
        },
        # 'django.db.backends': {  # All SQL
        #     'level': 'DEBUG' if DEBUG and DEV else 'WARNING',
        #     'handlers': ['file_sql'],
        #     'propagate': False,
        # },
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

if DEV and DEBUG:
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
# WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
