#!/bin/sh

python manage.py migrate

#python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); import django; django.setup()"
#
#echo "django inited for celerybeat"
#
#sleep 3

# --schedule=/srv/celerybeat-schedule --pidfile=/srv/celerybeat.pid
echo "Starting Celery Beat..."
python manage.py startbeat
#celery -A config beat --loglevel=warning --scheduler django_celery_beat.schedulers:DatabaseScheduler
