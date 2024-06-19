import csv
import re
from datetime import datetime
from io import StringIO


def calculate_age(birthdate_str: str) -> int:
    birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - birthdate.year
    # Был ли уже день рождения в этом году
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age


def get_number(value):
    pattern = re.compile(r'[0-9.,]+')
    matches = pattern.findall(value.replace('\xa0', ''))
    number_string = ''.join(matches).replace(',', '.')
    if number_string.count('.') > 1:
        parts = number_string.split('.')
        number_string = parts[0] + '.' + ''.join(parts[1:])

    return number_string


def create_virtual_csv(data) -> StringIO:
    """
    Создает виртуальный CSV файл из предоставленных данных.
    :param data: Массив данных, где каждый подмассив - это строка CSV.
    :return: Объект StringIO с содержимым CSV файла.
    """
    string_buffer = StringIO()
    csv_writer = csv.writer(string_buffer)

    # Запись данных в CSV
    for row in data:
        csv_writer.writerow(row)

    string_buffer.seek(0)
    return string_buffer
