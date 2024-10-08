import logging
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from modules.pickler import Pickler as PicklerCache

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / 'data'
BASE_CACHE_DIR = BASE_DATA_DIR / 'cache'
BASE_TEMP_DIR = BASE_DATA_DIR / 'temp'
WHISPER_DIR = BASE_DATA_DIR / 'whisper'
WHISPER_MODELS_DIR = WHISPER_DIR / 'models'

# Environment helpers
env = os.environ.get

dotenv_path = os.path.join(BASE_DIR, '.env.prod')
load_dotenv(dotenv_path=dotenv_path)

# Basic settings
DEV = bool(int(env('DEV', 0)))
DEBUG = bool(int(env('DEBUG', 0)))
SECRET_KEY = env('SECRET_KEY', 'your-secret-key')
ALLOWED_HOSTS = ['localhost', env('MAIN_DOMAIN', '127.0.0.1')] + env('ALLOWED_HOSTS', '').split(',')
ROOT_URLCONF = 'apps.Core.urls'

# Security and domain settings
HTTPS = bool(int(env('HTTPS', 0)))
MAIN_DOMAIN = env('MAIN_DOMAIN', '127.0.0.1')
DOMAIN_URL = f'http{"s" if HTTPS else ""}://{MAIN_DOMAIN}'

# Database and cache
REDIS_BASE_URL = 'redis://127.0.0.1:6379/'
REDIS_URL = env('REDIS_URL', REDIS_BASE_URL + '0') if not DEV else 'redis://127.0.0.1:6379'
REDIS_CACHE_URL = env('REDIS_CACHE_URL', REDIS_BASE_URL + '1') if not DEV else 'redis://127.0.0.1:6379'
DJANGO_REDIS_LOGGER = 'RedisLogger'
DJANGO_REDIS_IGNORE_EXCEPTIONS = True
# SESSION_ENGINE = 'redis_sessions.session'
# SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 86400  # seconds 2 days
# SESSION_SAVE_EVERY_REQUEST = True
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [f'https://{MAIN_DOMAIN}']
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    f'https://{MAIN_DOMAIN}'
]

# Static and media files
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = True
MINIO_USE_HTTPS = False
if DEV:
    STATIC_ROOT = BASE_DIR.parent / 'static'
    MEDIA_ROOT = BASE_DIR.parent / 'media'
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
else:
    STATIC_ROOT = None
    MEDIA_ROOT = None
    STATIC_URL = f'{DOMAIN_URL}/static/'
    MEDIA_URL = f'{DOMAIN_URL}/media/'

    MINIO_ENDPOINT = 'minio:9000'
    MINIO_EXTERNAL_ENDPOINT = f'{MAIN_DOMAIN}'  # For external access use Docker hostname and MinIO port
    MINIO_ACCESS_KEY = env('MINIO_ROOT_USER')
    MINIO_SECRET_KEY = env('MINIO_ROOT_PASSWORD')
    MINIO_EXTERNAL_ENDPOINT_USE_HTTPS = bool(int(env('MINIO_EXTERNAL_ENDPOINT_USE_HTTPS') or 0))
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
    MINIO_STATIC_FILES_BUCKET = 'static'  # Just bucket name may be 'my-static-files'?
    MINIO_MEDIA_FILES_BUCKET = 'media'  # Just bucket name may be 'media-files'?
    MINIO_BUCKET_CHECK_ON_SAVE = True  # Default: True // Creates a cart if it doesn't exist, then saves it
    MINIO_PUBLIC_BUCKETS.append(MINIO_STATIC_FILES_BUCKET)
    MINIO_PUBLIC_BUCKETS.append(MINIO_MEDIA_FILES_BUCKET)
    MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
    MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True
    DEFAULT_FILE_STORAGE = 'django_minio_backend.models.MinioBackend'
    STATICFILES_STORAGE = 'django_minio_backend.models.MinioBackendStatic'
    FILE_UPLOAD_MAX_MEMORY_SIZE = 65536

# Celery
# CELERY_BROKER_URL = REDIS_URL
# CELERY_RESULT_BACKEND = REDIS_URL
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# Celery
CELERY_BROKER_URL = f'amqp://guest:guest@{"rabbitmq" if not DEV else "localhost"}:5672//'
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('TZ', 'Europe/Moscow')
USE_I18N = True
USE_TZ = True

# Additional settings
SERVICE_ROOT = BASE_DIR / 'modules'
DEVELOPER_EMAIL = 'ivanhvalevskey@gmail.com'
HOLLIHOP_DOMAIN = env('HOLLIHOP_DOMAIN')
HOLLIHOP_AUTHKEY = env('HOLLIHOP_AUTHKEY')
TEACHER_SALARY_PASSWORD = env('TEACHER_SALARY_PASSWORD')
AMOLINK_NOTHING_FIT_INTRODUCTION_GROUPS = env('AMOLINK_NOTHING_FIT_INTRODUCTION_GROUPS')
AMOLINK_REPORT_JOIN_TO_INTRODUCTION_GROUPS = env('AMOLINK_REPORT_JOIN_TO_INTRODUCTION_GROUPS')
AMOLINK_REPORT_CALL_TRANSCRIBTION = env('AMOLINK_REPORT_CALL_TRANSCRIBTION')
GPT_TOKEN = env('GPT_TOKEN')
# Google Sheets
GOOGLE_API_JSON_CREDS_PATH = BASE_DIR / env('GSCREDS_FILE_NAME', '__NONE__')
GSDOCID_LOG_JOIN_FORMING_GROUPS = env('GSDOCID_LOG_JOIN_FORMING_GROUPS', '__NONE__')
GSDOCID_LOG_JOIN_FORMING_GROUPS_AUTUMN = env('GSDOCID_LOG_JOIN_FORMING_GROUPS_AUTUMN', '__NONE__')
GSDOCID_TEACHERS_SALARY = env('GSDOCID_TEACHERS_SALARY', '__NONE__')
GSDOCID_UPLOAD_BY_LESSON = env('GSDOCID_UPLOAD_BY_LESSON', '__NONE__')
GSDOCID_TRANSCRIBE_LEAD_CALL = env('GSDOCID_TRANSCRIBE_LEAD_CALL', '__NONE__')
GSDOCID_UPLOAD_BY_LAST_THEMES = (env('GSDOCID_UPLOAD_BY_LAST_THEMES', '__NONE__'), 'Lasts Themes')
GSDOCID_UPLOAD_AVERAGE_PRICE_PER_LESSON_STUDENT = (
    env('GSDOCID_UPLOAD_AVERAGE_PRICE_PER_LESSON_STUDENT', '__NONE__'),
    'Средняя цена за урок'
)
TABLE_TEACHERS_SALARY = (GSDOCID_TEACHERS_SALARY, '957421404')

# Courses
GSDOCID_COURSES_RESUME = env('GSDOCID_COURSES_RESUME', '__NONE__')

ALLOWED_DAYS_FOR_LESSON_REPORT = 30

LOGIN_URL = '/login/'

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',

    'corsheaders',
    'rest_framework',
    'adrf',
    # 'channels',
    'django_celery_beat',

    'apps.link_shorter',
    'apps.Core',
    'apps.tools',
    'apps.transcribe',
    'apps.endpoints',
]

if DEV:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': env('SQL_ENGINE'),
            'NAME': env('POSTGRES_DB'),
            'USER': env('POSTGRES_USER'),
            'PASSWORD': env('POSTGRES_PASSWORD'),
            'HOST': env('SQL_HOST'),
            'PORT': env('POSTGRES_PORT'),
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

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
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
LOG_PREFIX = env('LOG_PREFIX', 'server')
logs_prod_dir = os.path.join(BASE_DIR, 'logs/django_prod', LOG_PREFIX)
logs_dev_dir = os.path.join(BASE_DIR, 'logs/django_dev', LOG_PREFIX)
logs_sql_prod_dir = os.path.join(logs_prod_dir, 'sql')
logs_sql_dev_dir = os.path.join(logs_dev_dir, 'sql')

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
            'level': 'DEBUG' if DEBUG and DEV else 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(logs_sql_dev_dir if DEBUG and DEV else logs_sql_prod_dir, 'sql.log'),
            'when': 'midnight',
            'backupCount': 30,  # How many days to keep logs
            'formatter': 'base_formatter',
            'encoding': 'utf-8',
        },
        'file': {
            'level': 'DEBUG' if DEBUG and DEV else 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(logs_dev_dir if DEBUG and DEV else logs_prod_dir, 'django.log'),
            'when': 'midnight',
            'backupCount': 30,  # How many days to keep logs
            'formatter': 'base_formatter',
            'encoding': 'utf-8',
        },
        'console': {
            'level': 'DEBUG' if DEBUG and DEV else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'base_formatter',
        },
    },
    'loggers': {
        'base': {
            'handlers': ['console', 'file'] if not DEV else ['console'],
            'level': 'DEBUG' if DEBUG and DEV else 'INFO',
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
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
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
WSGI_APPLICATION = None  # 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

PICKLER_SETTINGS = {
    'base_temp_dir': BASE_CACHE_DIR,
    'separator': '--',
    'auto_delete_expired': True,
}
log = logging.getLogger('base')

log.info('#####################################')
log.info('########## Server Settings ##########')
log.info('#####################################')
log.info(f'{BASE_DIR=}')
log.info(f'{MAIN_DOMAIN=}')
log.info(f'{HTTPS=}')
# log.info(f'{MINIO_EXTERNAL_ENDPOINT_USE_HTTPS=}')
# log.info(f'{MINIO_USE_HTTPS=}')
log.info(f'{ALLOWED_HOSTS=}')
log.info(f'{DEBUG=}')
log.info(f'{DEV=}')
log.info(f'{ASGI_APPLICATION=}')
log.info(f'{WSGI_APPLICATION=}')
log.info(f'{STATIC_URL=}')
log.info(f'{MEDIA_URL=}')
log.info(f'{STATIC_ROOT=}')
log.info(f'{MEDIA_ROOT=}')
log.info('#####################################')
log.info('#####################################')
log.info('#####################################')
