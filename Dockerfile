FROM python:3.11-alpine as base

COPY . /srv
WORKDIR /srv

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update
RUN apk add dos2unix
RUN apk add libpq-dev
RUN apk add netcat-openbsd
RUN python -m venv /venv
ENV PATH="/srv/venv/bin:$PATH"
RUN python -m pip install --upgrade pip
RUN python -m pip install -r /srv/requirements.txt
RUN dos2unix /srv/entrypoint.prod.sh
RUN apk del dos2unix
RUN chmod +x /srv/entrypoint.prod.sh

RUN python manage.py collectstatic --noinput
#################################
# Стадия подготовки Nginx образа
#################################
FROM nginx:alpine AS nginx
# Копирование статических файлов из предыдущей стадии
COPY --from=base /static /static
COPY --from=base /media /media
# Копирование конфигурации Nginx (если есть изменения)
COPY ./nginx.conf /etc/nginx/conf.d/default.conf


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