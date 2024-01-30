import requests
from django.db import connections
from django.http import HttpResponse
from django.shortcuts import render
import logging

from django_redis import get_redis_connection

log = logging.getLogger('Core')


def menu(request):
    return render(request, 'Core/menu.html')


def health_test(request):
    # Проверка Redis
    if not get_redis_connection().flushall():
        log.warning('Redis have not yet come to life')
        return HttpResponse("Redis error", status=500)

    # Проверка базы данных PostgreSQL
    try:
        connections['default'].cursor()
    except Exception as e:
        log.warning(f'Postgres have not yet come to life: {str(e)}')
        return HttpResponse(f"Postgres error: {str(e)}", status=500)

    log.warning('Web Server Alive')
    return HttpResponse("OK")
