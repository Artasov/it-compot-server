import logging

from django.db import connections
from django.http import HttpResponse
from django.shortcuts import render
from django_minio_backend import MinioBackend
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

    minio_available = MinioBackend().is_minio_available()  # An empty string is fine this time
    if not minio_available:
        log.error(f'MINIO ERROR')
        log.info(minio_available.details)
        log.info(f'MINIO_STATIC_FILES_BUCKET = {MinioBackend().MINIO_STATIC_FILES_BUCKET}')
        log.info(f'MINIO_MEDIA_FILES_BUCKET = {MinioBackend().MINIO_MEDIA_FILES_BUCKET}')
        log.info(f'base_url = {MinioBackend().base_url}')
        log.info(f'base_url_external = {MinioBackend().base_url_external}')
        log.info(f'HTTP_CLIENT = {MinioBackend().HTTP_CLIENT}')
        return HttpResponse(f"MINIO ERROR", status=500)
    return HttpResponse("OK")
