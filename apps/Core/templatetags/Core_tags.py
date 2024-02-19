from django import template

# from apps.Core.forms import UserLoginForm
# from apps.Core.models import CompanyData

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
