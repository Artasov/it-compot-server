import functools
import logging
from time import time

from aiohttp import ClientConnectorError
from django.conf import settings
from django.contrib.auth import logout
from django.core.handlers.asgi import ASGIRequest
from django.core.handlers.wsgi import WSGIRequest
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response

log = logging.getLogger('base')


def allowed_only(allowed_methods: list[str, ...] | tuple[str, ...]):
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if request.method in allowed_methods:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseNotAllowed(allowed_methods)

        return wrapped_view

    return decorator


def semaphore_handler(fn) -> callable:
    @functools.wraps(fn)
    async def inner(request: ASGIRequest, *args, **kwargs):
        try:
            return await fn(request, *args, **kwargs)
        except ClientConnectorError as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return inner


def acontroller(name=None, log_time=False) -> callable:
    def decorator(fn) -> callable:
        @functools.wraps(fn)
        async def inner(request: ASGIRequest, *args, **kwargs):
            fn_name = name or fn.__name__
            log.info(f'Async Controller: {request.method} | {fn_name}')
            if log_time:
                start_time = time()

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


def atimer(name=None) -> callable:
    def decorator(fn) -> callable:
        @functools.wraps(fn)
        async def inner(request: WSGIRequest, *args, **kwargs):
            result = await fn(request, *args, **kwargs)
            end_time = time()
            elapsed_time = end_time - start_time
            fn_name = name or fn.__name__
            log.info(f"Execution time of {fn_name}: {elapsed_time:.2f} seconds")
            return result

        return inner

    return decorator


def controller(name=None) -> callable:
    def decorator(fn) -> callable:
        @functools.wraps(fn)
        def inner(request: WSGIRequest, *args, **kwargs):
            fn_name = name or fn.view_class.__name__ if fn.__name__ == 'view' else fn.__name__
            log.info(f'Controller: {request.method} | {fn_name}')

            if settings.DEBUG:
                with transaction.atomic():
                    return fn(request, *args, **kwargs)
            else:
                try:
                    with transaction.atomic():
                        return fn(request, *args, **kwargs)
                except Exception as e:
                    log.critical(f"ERROR in {fn_name}: {str(e)}", exc_info=True)
                    raise

        return inner

    return decorator


def timer(name=None) -> callable:
    def decorator(fn) -> callable:
        @functools.wraps(fn)
        def inner(request: WSGIRequest, *args, **kwargs):
            start_time = time()
            result = fn(request, *args, **kwargs)
            end_time = time()
            elapsed_time = end_time - start_time
            fn_name = name or fn.view_class.__name__ if fn.__name__ == 'view' else fn.__name__
            log.info(f"Execution time of {fn_name}: {elapsed_time:.2f} seconds")
            return result

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
