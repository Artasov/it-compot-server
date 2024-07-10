import aiohttp
from aiohttp import FormData
from django.conf import settings


class Whisper:
    def __init__(self, token: str = settings.GPT_TOKEN, proxy: str | None = None):
        self.token = token
        self.proxy = proxy

    async def _send_request(self,
                            url: str,
                            method: str = 'POST',
                            data: dict | FormData = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                    method=method,
                    url=url,
                    headers={'Authorization': f'Bearer {self.token}'},
                    data=data,
                    proxy=self.proxy  # Указываем прокси здесь
            ) as response:
                response_data = await response.json()
                return response_data

    async def transcribe_audio(self, path: str) -> str:
        with open(path, 'rb') as f:
            audio_data = f.read()

        data = FormData()
        data.add_field('file', audio_data, filename='audio.mp3', content_type='audio/mpeg')
        data.add_field('model', 'whisper-1')

        response_data = await self._send_request(
            url='https://api.openai.com/v1/audio/transcriptions',
            data=data
        )
        return response_data.get('text', '')
