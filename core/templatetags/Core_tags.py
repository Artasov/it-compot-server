from datetime import timedelta

from django import template
from django.utils import timezone
from django.utils.datetime_safe import datetime

# from Core.forms import UserLoginForm
# from Core.models import CompanyData
from core.services.services import get_plural_form_number

register = template.Library()


# @register.simple_tag()
# def get_login_form():
#    return UserLoginForm()


# @register.simple_tag()
# def get_company_data(company_data_param: str):
#     try:
#         return CompanyData.objects.get(param=company_data_param).value
#     except CompanyData.DoesNotExist:
#         return f'"{company_data_param}" not found in CompanyData.'


@register.filter
def remove_colons(value):
    if value:
        return value.replace(":", "")
    return value


@register.filter
def time_since(value):
    now = datetime.now(timezone.utc)
    value = value.replace(tzinfo=timezone.utc)
    delta = now - value
    if delta <= timedelta(minutes=1):
        return 'Минуту назад'
    elif delta <= timedelta(hours=1):
        minutes = delta.seconds // 60
        plural_form = get_plural_form_number(minutes, ('минуту', 'минуты', 'минут'))
        return f'{minutes} {plural_form} назад'
    elif delta <= timedelta(days=1):
        hours = delta.seconds // 3600
        plural_form = get_plural_form_number(hours, ('час', 'часа', 'часов'))
        return f'{hours} {plural_form} назад'
    elif delta <= timedelta(days=30):
        days = delta.days
        plural_form = get_plural_form_number(days, ('день', 'дня', 'дней'))
        return f'{days} {plural_form} назад'
    elif delta <= timedelta(days=365):
        months = delta.days // 30
        plural_form = get_plural_form_number(months, ('месяц', 'месяца', 'месяцев'))
        return f'{months} {plural_form} назад'
    else:
        years = delta.days // 365
        plural_form = get_plural_form_number(years, ('год', 'года', 'лет'))
        return f'{years} {plural_form} назад'
