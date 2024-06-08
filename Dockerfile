FROM python:3.11-alpine as base

COPY . /srv
WORKDIR /srv

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update
RUN apk add dos2unix
RUN apk add libpq-dev
RUN apk add netcat-openbsd
# RUN python -m venv /venv
# ENV PATH="/srv/venv/bin:$PATH"
RUN python -m pip install --upgrade pip
RUN python -m pip install -r /srv/requirements.txt
RUN dos2unix /srv/entrypoint.prod.sh
RUN apk del dos2unix
RUN chmod +x /srv/entrypoint.prod.sh

# Установка Chrony для синхронизации времени
RUN apk add --no-cache chrony
# Запуск Chrony и настройка времени при старте контейнера
RUN echo "server pool.ntp.org iburst" >> /etc/chrony/chrony.conf

# Установка Supervisor
RUN apk update && apk add supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

###########
# DEV #
###########
FROM base as dev
ENTRYPOINT ["sh", "/srv/entrypoint.dev.sh"]

#############
# PROD #
#############
FROM base as prod
ENTRYPOINT ["sh", "/srv/entrypoint.prod.sh"]

#############
# CELERY #
#############
FROM base as celery

RUN adduser -D celeryuser
USER celeryuser

ENTRYPOINT ["sh", "/srv/entrypoint_celery.sh"]