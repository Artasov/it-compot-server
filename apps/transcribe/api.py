import logging
import os

from adrf.decorators import api_view
from django.conf import settings
from rest_framework.response import Response

from apps.Core.services.base import acontroller
from apps.transcribe.serializers import AmoCallTranscribeSerializer
from modules.common.common import download_file
from modules.gpt.classes.whisper import Whisper
from modules.gsheet.classes.gsheetsclient import GSDocument
from modules.pickler import Pickler

log = logging.getLogger('base')
pickler = Pickler(**settings.PICKLER_SETTINGS)


@acontroller('Транскрибация звонка клиента')
@api_view(('GET', 'POST',))
async def transcribe_lead_call(request):
    print(request.data)
    serializer = AmoCallTranscribeSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        temp_file_path = await download_file(data['call_audio_url'])
        whisper = Whisper(
            proxy='http://user203097:50y9sd@140.99.236.87:1848'
        )
        transcript = await whisper.transcribe_audio(temp_file_path)
        print('RECOGNITION')
        print(transcript)
        os.remove(temp_file_path)
        GSDocument(settings.GSDOCID_TRANSCRIBE_LEAD_CALL).append_row(
            sheet_name='All',
            row=(
                f'https://itbestonlineschool.amocrm.ru/leads/detail/{data["lead_id"]}',
                f'https://itbestonlineschool.amocrm.ru/contacts/detail/{data["contact_id"]}',
                transcript,
                data['call_audio_url'],
                data.get('responsible'),
                data.get('duration'),
                data.get('status'),
                data.get('reason'),
            ),
        )
        return Response({'success': True}, 200)
    else:
        print(serializer.errors)
        return Response({'success': False}, 400)
