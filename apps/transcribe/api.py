import logging

from adrf.decorators import api_view
from django.conf import settings
from rest_framework.response import Response

from apps.Core.services.base import acontroller
from modules.pickler import Pickler

log = logging.getLogger('base')
pickler = Pickler(**settings.PICKLER_SETTINGS)


@acontroller('Транскрибация звонка клиента')
@api_view(('GET',))
async def transcribe_lead_call(request):
    # temp_file_path = await download_file(
    #     'https://media.uiscom.ru/3960098281/2e40c75469075b6e5f16cd29873cbc57'
    # )
    # whisper = Whisper(
    #     proxy='http://user159222:fmvjbk@163.5.226.88:2127'
    # )
    # transcript = await whisper.transcribe_audio(temp_file_path)
    # print(transcript)
    # serializer = AmoCallTranscribeSerializer(data=request.data)
    # serializer.is_valid(raise_exception=True)
    # data = serializer.validated_data
    # temp_file_path = await download_file(data['call_audio_url'])
    # transcribe_lead_call_task.delay(
    #     lead_id=data['lead_id'],
    #     contact_id=data['contact_id'],
    #     temp_file_path=temp_file_path,
    #     language='ru'
    # )
    return Response({'success': True}, 200)
