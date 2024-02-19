from adrf.serializers import Serializer as AsyncSerializer
from django.conf import settings
from rest_framework import serializers

from apps.link_shorter.services.common import create_short_link

serializers.CharField()


class LinkSerializer(AsyncSerializer):
    url = serializers.URLField()

    def validate_url(self, value):
        """
        Check that the URL contains the required domain.
        """
        if settings.MAIN_DOMAIN not in value:
            raise serializers.ValidationError("Only URLs containing the domain are allowed.")
        return value

