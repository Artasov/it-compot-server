import csv
import os
import re
from datetime import datetime
from io import StringIO
from urllib.parse import urlparse

import aiohttp
from django.conf import settings


def now_date():
    return datetime.now().strftime("%Y-%m-%d")


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


async def download_file(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            if response.status == 200:
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition and 'filename=' in content_disposition:
                    file_name = content_disposition.split('filename=')[1].strip('"')
                else:
                    parsed_url = urlparse(url)
                    file_name = os.path.basename(parsed_url.path)
                file_path = settings.BASE_TEMP_DIR / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                if file_path.exists(): return str(file_path)
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
            else:
                raise Exception(f"Failed to download file from {url}. Status code: {response.status}")

    return str(file_path)
