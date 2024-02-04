#!/bin/sh

############
#   PROD   #
############
/usr/sbin/chronyd

chronyc tracking
# Collect static files into one folder without asking for confirmation
python manage.py collectstatic --noinput &&
# Apply migrations to the database
python manage.py migrate
#python manage.py runserver
# Bind gunicorn

#daphne config.asgi:application --port 8000 --bind 0.0.0.0
gunicorn config.wsgi:application --workers 1 --bind 0.0.0.0:8000 --timeout 60 --max-requests 1000
#uvicorn config.asgi:application --host 0.0.0.0 --port 8000
