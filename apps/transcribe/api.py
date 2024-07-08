import logging

from adrf.decorators import api_view
from django.conf import settings
from rest_framework.response import Response

from apps.Core.services.base import acontroller
from apps.transcribe.tasks.base import transcribe_lead_call_task
from service.pickler import Pickler
from transcribe.serializers import AmoCallTranscribeSerializer
from transcribe.services.common import download_audio, transcribe

log = logging.getLogger('base')
pickler = Pickler(**settings.PICKLER_SETTINGS)


@acontroller('Транскрибация звонка клиента')
@api_view(('GET',))
async def transcribe_lead_call(request):
    # temp_file_path = await download_audio(
    #     'https://media.uiscom.ru/3960098281/2e40c75469075b6e5f16cd29873cbc57'
    # )
    # print(temp_file_path)
    print(transcribe(
        r'E:/nonExistence/Code/Web/iTCompot/config/data/temp/1.mp3'
    ))
    # serializer = AmoCallTranscribeSerializer(data=request.data)
    # serializer.is_valid(raise_exception=True)
    # data = serializer.validated_data
    # temp_file_path = await download_audio(data['call_audio_url'])
    # transcribe_lead_call_task.delay(
    #     lead_id=data['lead_id'],
    #     contact_id=data['contact_id'],
    #     temp_file_path=temp_file_path,
    #     language='ru'
    # )
    return Response({'success': True}, 200)
