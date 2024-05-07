from django import template

register = template.Library()


@register.filter(name='month_to_russian')
def month_to_russian(value):
    """
    Преобразует формат месяца 'YYYY-MM' в русское название месяца с годом.
    """
    try:
        year, month = map(int, value.split('-'))
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        month_name = months[month - 1]
        return f"{month_name}"
    except ValueError:
        return value
