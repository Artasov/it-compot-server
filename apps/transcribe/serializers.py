from adrf.serializers import Serializer as AsyncSerializer
from rest_framework import serializers


class AmoCallTranscribeSerializer(AsyncSerializer):
    lead_id = serializers.CharField(max_length=50)
    contact_id = serializers.CharField(max_length=50)
    call_audio_url = serializers.CharField(max_length=500)
    responsible = serializers.CharField(max_length=500, required=False)
    duration = serializers.CharField(max_length=30, required=False)
    status = serializers.CharField(max_length=150, required=False)
    reason = serializers.CharField(max_length=500, required=False)
