from adrf.serializers import Serializer as AsyncSerializer
from rest_framework import serializers


class AmoCallTranscribeSerializer(AsyncSerializer):
    lead_id = serializers.IntegerField()
    contact_id = serializers.IntegerField()
    call_audio_url = serializers.CharField(max_length=500)
