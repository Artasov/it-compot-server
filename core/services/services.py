import functools
import hashlib
import hmac
import json
import os
import time
import traceback
import urllib
from typing import Optional, Tuple, List

from django.conf import settings
from django.contrib.auth import logout
from django.db import transaction
from django.shortcuts import render, redirect

from config.settings import DEVELOPER_EMAIL
from mailing.services.services import send_text_email
from core.error_messages import USER_EMAIL_NOT_EXISTS, USER_USERNAME_NOT_EXISTS
import urllib.parse, urllib.request
from django.http import HttpResponseNotAllowed, HttpResponse


def reCAPTCHA_validation(request):
    recaptcha_response = request.POST.get('g-recaptcha-response')
    url = 'https://www.google.com/recaptcha/api/siteverify'
    values = {
        'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }
    data = urllib.parse.urlencode(values).encode()
    req = urllib.request.Request(url, data=data)
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    return result


def int_decrease_by_percentage(num: int, percent: int) -> int:
    if percent == 0:
        return num
    return round(num - (num / 100 * float(percent)))


def get_plural_form_number(number: int, forms: tuple):
    """get_plural_form_number(minutes, ('минуту', 'минуты', 'минут'))"""
    if number % 10 == 1 and number % 100 != 11:
        return forms[0]
    elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
        return forms[1]
    else:
        return forms[2]


# def get_user_by_email_or_name(email_or_name: str) -> Tuple[Optional[User], str]:
#     """Если пользователь не найден вернется None и строка ошибки, иначе User и пустая строка"""
#     user_ = None
#     error = ''
#     if '@' in email_or_name:
#         try:
#             user_ = User.objects.get(email=email_or_name)
#         except User.DoesNotExist:
#             error = USER_EMAIL_NOT_EXISTS
#     else:
#         try:
#             user_ = User.objects.get(username=email_or_name)
#         except User.DoesNotExist:
#             error = USER_USERNAME_NOT_EXISTS
#
#     return user_, error


def check_recaptcha_is_valid(recaptcha_response: str) -> bool:
    if not recaptcha_response:
        return False
    url = 'https://www.google.com/recaptcha/api/siteverify'
    values = {
        'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }
    data = urllib.parse.urlencode(values).encode()
    req = urllib.request.Request(url, data=data)
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    recaptcha_is_valid = result.get('success', False)
    if not recaptcha_is_valid:
        return False
    return True


def allowed_only(allowed_methods):
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if request.method in allowed_methods:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseNotAllowed(allowed_methods)

        return wrapped_view

    return decorator


def base_view(fn):
    """transaction.atomic() и хук исключений самого высокого уровня"""

    @functools.wraps(fn)
    def inner(request, *args, **kwargs):
        if settings.DEBUG:
            with transaction.atomic():
                return fn(request, *args, **kwargs)
        else:
            try:
                with transaction.atomic():
                    return fn(request, *args, **kwargs)
            except Exception as e:
                send_text_email(
                    subject='Ошибка на сервере',
                    to_email=settings.DEVELOPER_EMAIL,
                    text=f"error_message: {str(e)}\n"
                         f"traceback:\n{traceback.format_exc()}"
                )
                return HttpResponse(f'Произошла ошибка, свяжитесь с нами tg=@artasov email={DEVELOPER_EMAIL}')

    return inner


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
