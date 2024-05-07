import functools
import logging
from time import time

from aiohttp import ClientConnectorError
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import Group
from django.core.handlers.asgi import ASGIRequest
from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response

log = logging.getLogger('base')


def add_user_to_group(user, group_name):
    group, created = Group.objects.get_or_create(name=group_name)
    if user not in group.user_set.all():
        group.user_set.add(user)


def allowed_only(allowed_methods: list[str, ...] | tuple[str, ...]):
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if request.method in allowed_methods:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseNotAllowed(allowed_methods)

        return wrapped_view

    return decorator


def asemaphore_handler(fn) -> callable:
    @functools.wraps(fn)
    async def inner(request: ASGIRequest, *args, **kwargs):
        try:
            return await fn(request, *args, **kwargs)
        except ClientConnectorError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return inner


def semaphore_handler(fn) -> callable:
    @functools.wraps(fn)
    def inner(request: WSGIRequest, *args, **kwargs):
        try:
            return fn(request, *args, **kwargs)
        except ClientConnectorError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return inner


def acontroller(name=None, log_time=False, auth: bool = False) -> callable:
    def decorator(fn) -> callable:
        @functools.wraps(fn)
        async def inner(request: ASGIRequest, *args, **kwargs):
            fn_name = name or fn.__name__
            log.info(f'Async Controller: {request.method} | {fn_name}')
            if log_time:
                start_time = time()

            if auth:
                is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
                if not is_authenticated:
                    return redirect(settings.LOGIN_URL)

            if settings.DEBUG:
                return await fn(request, *args, **kwargs)
            else:
                try:
                    if log_time:
                        end_time = time()
                        elapsed_time = end_time - start_time
                        log.info(f"Execution time of {fn_name}: {elapsed_time:.2f} seconds")
                    return await fn(request, *args, **kwargs)
                except Exception as e:
                    log.critical(f"ERROR in {fn_name}: {str(e)}", exc_info=True)
                    raise e

        return inner

    return decorator


def controller(name=None, log_time=False, auth=False) -> callable:
    def decorator(fn) -> callable:
        @functools.wraps(fn)
        def inner(request: WSGIRequest, *args, **kwargs):
            fn_name = name or fn.__name__
            log.info(f'Sync Controller: {request.method} | {fn_name}')
            if log_time:
                start_time = time()
            if auth:
                if not request.user.is_authenticated:
                    return redirect(settings.LOGIN_URL)
            if settings.DEBUG:
                with transaction.atomic():
                    return fn(request, *args, **kwargs)
            else:
                try:
                    if log_time:
                        end_time = time()
                        elapsed_time = end_time - start_time
                        log.info(f"Execution time of {fn_name}: {elapsed_time:.2f} seconds")
                    with transaction.atomic():
                        return fn(request, *args, **kwargs)
                except Exception as e:
                    log.critical(f"ERROR in {fn_name}: {str(e)}", exc_info=True)
                    raise e

        return inner

    return decorator


def forbidden_with_login(fn, redirect_field_name: str = None):
    """logout if user.is_authenticated, with redirect if necessary"""

    @functools.wraps(fn)
    def inner(request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            if redirect_field_name is not None:
                return redirect(redirect_field_name)
            return fn(request, *args, **kwargs)
        else:
            return fn(request, *args, **kwargs)

    return inner
