from adrf.decorators import api_view
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework.response import Response

from apps.Core.services.common import acontroller
from .models import ShortLink
from .serializers import LinkSerializer
from .services.common import create_short_link


@acontroller('Сокращение ссылки', True)
@api_view(('POST',))
async def create_short_link_controller(request) -> HttpResponse:
    serializer = LinkSerializer(data=request.data)
    if serializer.is_valid():
        return HttpResponse(
            (await create_short_link(serializer.validated_data.get('url'))).get_short_url()
        )
    else:
        return Response(serializer.errors, status=400)


def redirect_to_full_link(request, short_code) -> HttpResponseRedirect:
    link = get_object_or_404(ShortLink, short_code=short_code)
    return redirect(link.original_url)
