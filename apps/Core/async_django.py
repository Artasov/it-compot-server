from functools import wraps
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.db.transaction import Atomic
from django.shortcuts import resolve_url


class AsyncAtomicContextManager(Atomic):
    def __init__(self, using=None, savepoint=True, durable=False):
        super().__init__(using, savepoint, durable)

    async def __aenter__(self):
        await sync_to_async(super().__enter__)()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await sync_to_async(super().__exit__)(exc_type, exc_value, traceback)


def aatomic(fun, *args, **kwargs) -> callable:
    async def wrapper():
        async with AsyncAtomicContextManager():
            await fun(*args, **kwargs)

    return wrapper


async def arelated(model_object, related_field_name: str):
    return await sync_to_async(getattr)(model_object, related_field_name, None)


async def aall(queryset) -> list:
    return await sync_to_async(list)(queryset.all())


async def afilter(queryset, *args, **kwargs) -> list:
    return await sync_to_async(list)(queryset.filter(*args, **kwargs))


def auser_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    if not login_url:
        login_url = settings.LOGIN_URL

    def decorator(view_func):
        @wraps(view_func)
        async def _wrapped_view(request, *args, **kwargs):
            if await test_func(request.user):
                return await view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url)
            # If the login_url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            return redirect_to_login(path, resolved_login_url, redirect_field_name)

        return _wrapped_view

    return decorator


def alogin_required(
        function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = auser_passes_test(
        sync_to_async(lambda u: u.is_authenticated),
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
