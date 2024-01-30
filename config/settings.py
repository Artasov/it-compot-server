import os
from pathlib import Path

env = os.environ.get
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DATA_DIR = BASE_DIR / 'data'
HTTPS = bool(int(env('HTTPS') or 0))
MAIN_DOMAIN = str(env('MAIN_DOMAIN') or '127.0.0.1')
ALLOWED_HOSTS = str((env('ALLOWED_HOSTS') or '') + f',{MAIN_DOMAIN}').split(',')
ALLOWED_HOSTS.append('localhost')
ROOT_URLCONF = 'Core.urls'
SECRET_KEY = env('SECRET_KEY')
DEBUG = bool(int(env('DEBUG')))
DEV = bool(int(env('DEV')))
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR.parent / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'Core' / 'static',
]
if DEBUG:
    MEDIA_URL = '/media/'
else:
    MEDIA_URL = '/static/media/'
MEDIA_ROOT = BASE_DIR.parent / 'static' / 'media'

SERVICE_ROOT = BASE_DIR / 'service'

DEVELOPER_EMAIL = 'ivanhvalevskey@gmail.com'

# HolliHop
HOLLIHOP_DOMAIN = 'it-school.t8s.ru'
HOLLIHOP_AUTHKEY = env('AUTHKEY')

# GSheets
# (table_id, list_id)
TABLE_TEACHERS_SALARY = ('1T5Np2RdqBCdmo7IUm9FGBG6mZWY138arUWPJOBs-slY', '690189137')

# Other
TEACHER_SALARY_PASSWORD = env('TEACHER_SALARY_PASSWORD')

GOOGLE_API_JSON_CREDS_PATH = os.path.join(BASE_DIR, 'it-compot-web-client_creds.json')

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

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
