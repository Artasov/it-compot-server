import logging

from adrf.decorators import api_view
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import alogout, aauthenticate, alogin
from django.contrib.auth.models import User
from django.db import connections
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django_minio_backend import MinioBackend
from django_redis import get_redis_connection
from rest_framework.decorators import permission_classes
from rest_framework.response import Response

from apps.Core.async_django import alogin_required
from apps.Core.permissions import IsStaff
from apps.Core.services.base import add_user_to_group, acontroller
from apps.Core.tasks.cache_tasks import pickler_delete_expired_cache, pickler_delete_all_cache
from apps.tools.forms.teachers_salary import StupidAuthForm

log = logging.getLogger('base')


@api_view(('GET',))
@permission_classes((IsStaff,))
async def delete_expired_cache(request):
    pickler_delete_expired_cache.delay()
    return Response('Cache EXPIRED clear task initiated.', status=200)


@api_view(('GET',))
@permission_classes((IsStaff,))
async def delete_all_cache(request):
    pickler_delete_all_cache.delay()
    return Response('Cache ALL clear task initiated.', status=200)


async def signout(request):
    await alogout(request)
    return redirect('stupid_auth')


@acontroller('Тупая авторизация')
@api_view(('GET', 'POST'))
async def stupid_auth(request) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('menu')
    form = StupidAuthForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data['email']
        username = email.split('@')[0]
        password = form.cleaned_data['password']
        try:
            await User.objects.aget(email=email)
        except User.DoesNotExist:
            await sync_to_async(User.objects.create_user)(
                username=username, email=email,
                password=settings.TEACHER_SALARY_PASSWORD
            )
        user = await aauthenticate(request, username=username, password=password)
        if user:
            await alogin(request, user)
            await sync_to_async(add_user_to_group)(user, 'teacher')
            return redirect('menu')
        else:
            form.add_error(None, 'Что-то пошло не так.')
    return await sync_to_async(render)(request, 'Core/stupid_auth.html', {'form': form})


@alogin_required(login_url='/login/')
async def menu(request) -> HttpResponse:
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
        log.error(minio_available.details)
        log.error(f'MINIO_STATIC_FILES_BUCKET = {MinioBackend().MINIO_STATIC_FILES_BUCKET}')
        log.error(f'MINIO_MEDIA_FILES_BUCKET = {MinioBackend().MINIO_MEDIA_FILES_BUCKET}')
        log.error(f'base_url = {MinioBackend().base_url}')
        log.error(f'base_url_external = {MinioBackend().base_url_external}')
        log.error(f'HTTP_CLIENT = {MinioBackend().HTTP_CLIENT}')
        return HttpResponse(f"MINIO ERROR", status=500)
    return HttpResponse("OK")
