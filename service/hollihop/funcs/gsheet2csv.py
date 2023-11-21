import csv
from io import StringIO

import requests


def download_google_sheet_as_csv(spreadsheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code}")

    # Указываем кодировку
    data = StringIO(response.content.decode('utf-8'))
    csv_reader = csv.reader(data)

    # Преобразуем CSV данные в массив
    return list(csv_reader)
