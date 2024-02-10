import csv
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
