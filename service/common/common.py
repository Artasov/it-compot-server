import csv
from io import StringIO


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
