import csv
import logging
from io import StringIO

import aiohttp

log = logging.getLogger('base')


async def download_google_sheet_as_csv(spreadsheet_id: str, gid: str) -> list:
    """
    Download a GoogleSheet as csv file.
    @param spreadsheet_id: doc id
    @param gid: table id
    @return: list rows
    """
    url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    log.info(f'{url} to google sheet downloading...')
    print(f'{url} to google sheet downloading...')
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5000)) as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(response)
                raise Exception(f"Failed to fetch data: {response.status} {await response.text()}")
            content = await response.text()

    data = StringIO(content)
    csv_reader = csv.reader(data)
    return list(csv_reader)
