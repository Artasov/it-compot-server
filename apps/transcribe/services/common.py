import logging
import os
import shutil
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import requests
import whisper
from django.conf import settings

log = logging.getLogger('base')


async def download_audio(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition and 'filename=' in content_disposition:
                    file_name = content_disposition.split('filename=')[1].strip('"')
                else:
                    parsed_url = urlparse(url)
                    file_name = os.path.basename(parsed_url.path)
                file_path = Path(settings.BASE_TEMP_DIR) / file_name
                with open(file_path, 'wb') as f:
                    f.write(await response.read())
            else:
                raise Exception(f"Failed to download file from {url}. Status code: {response.status}")
    return str(file_path)


def transcribe(path: str, language: str = 'ru') -> str:
    if not os.path.isfile(path):
        raise Exception(f"File not found: {path}")
    if not shutil.which("ffmpeg"):
        raise Exception("ffmpeg not found in PATH")
    model = whisper.load_model(name='large-v3', download_root=str(settings.WHISPER_MODELS_DIR))
    options = whisper.DecodingOptions(language=language)
    result = model.transcribe(path, options=options)
    return result['text']


def send_transcribe_lead_call_report(lead_id: int, contact_id: int, text: str):
    response = requests.post(
        url='https://mysite.ru',
        json={
            'lead_id': lead_id,
            'contact_id': contact_id,
            'text': text
        },
        headers={
            'Content-Type': 'application/json'
        }
    )
    if response.status_code == 200:
        log.info("Send transcribe lead call report was successful")
    else:
        log.error(f"Failed to send transcribe lead call report, status code: {response.status_code}")
