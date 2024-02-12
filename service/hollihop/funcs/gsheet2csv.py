import csv
from io import StringIO

import aiohttp


async def download_google_sheet_as_csv(spreadsheet_id: str, gid: str) -> list:
    """
    Download a GoogleSheet as csv file.
    @param spreadsheet_id: doc id
    @param gid: table id
    @return: list rows
    """
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch data: {response.status}")
            content = await response.text()

    data = StringIO(content)
    csv_reader = csv.reader(data)
    return list(csv_reader)
