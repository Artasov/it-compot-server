import logging

from django.db import connections
from django.http import HttpResponse
from django.shortcuts import render
from django_redis import get_redis_connection

log = logging.getLogger('base')


def menu(request) -> HttpResponse:
    return render(request, 'Core/menu.html')


def health_test(request) -> HttpResponse:
    # Проверка Redis
    if not get_redis_connection().flushall():
        log.error('Redis have not yet come to life')
        return HttpResponse("Redis error", status=500)
    try:
        connections['default'].cursor()
    except Exception as e:
        log.error(f'DB have not yet come to life: {str(e)}')
        return HttpResponse(f"DB error: {str(e)}", status=500)

    return HttpResponse("OK")
