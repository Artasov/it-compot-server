from datetime import timedelta

from django import template
from django.utils import timezone

# from Core.forms import UserLoginForm
# from Core.models import CompanyData
from Core.services.services import get_plural_form_number

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

@register.simple_tag()
def get_beauty_int(price):
    price = str(int(price))
    done_str = ''
    count_symbols = 0
    for i in range(len(price) - 1, -1, -1):
        if count_symbols < 3:
            done_str += price[i]
            count_symbols += 1
        else:
            done_str += ' '
            done_str += price[i]
            count_symbols = 1
    return done_str[::-1]


@register.filter
def remove_colons(value):
    if value:
        return value.replace(":", "")
    return value


@register.filter
def time_since(value):
    now = timezone.now()
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
