import datetime
import logging
from urllib.parse import quote

from adrf.decorators import api_view
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from apps.Core.services.common import asemaphore_handler, acontroller
from apps.link_shorter.services.common import create_short_link
from apps.tools.serializers import (
    StudentAlreadyStudyingOnDisciplineSerializer,
    FormingGroupParamsSerializer,
    StudentToGroupSerializer,
    SendNothingFitSerializer,
    BuildLinkForJoinToFormingGroupSerializer,
)
from apps.tools.services.signup_group.funcs import (
    is_student_in_group_on_discipline,
    add_student_to_forming_group, send_nothing_fit_units_to_amo
)
from service.common.common import calculate_age

log = logging.getLogger('base')


@acontroller('Получение групп для записи на вводный модуль.', True)
@api_view(('GET',))
@asemaphore_handler
async def get_forming_groups_for_join(request) -> Response:
    serializer = FormingGroupParamsSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    from apps.tools.services.signup_group.funcs import get_forming_groups_for_join
    # В age можно передавать timestamp даты рождения или сразу возраст
    age_or_tsmp_birth = serializer.validated_data['age']
    return Response(await get_forming_groups_for_join(
        level=serializer.validated_data['level'],
        discipline=serializer.validated_data['discipline'],
        age=calculate_age(
            datetime.datetime.fromtimestamp(age_or_tsmp_birth).strftime('%Y-%m-%d')
        ) if age_or_tsmp_birth > 100 else age_or_tsmp_birth,
    ), status=status.HTTP_200_OK)


@acontroller('Добавление ученика на вводный модуль', True)
@api_view(('POST',))
@asemaphore_handler
async def student_to_forming_group(request) -> Response:
    serializer = StudentToGroupSerializer(data=request.POST)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    result: bool = await add_student_to_forming_group(
        student_id=serializer.validated_data.get('student_id'),
        group_id=serializer.validated_data.get('group_id')
    )
    return Response(data={'success': result},
                    status=status.HTTP_200_OK if result
                    else status.HTTP_400_BAD_REQUEST)


@acontroller('Проверка записан ли уже ученик', True)
@api_view(('GET',))
@asemaphore_handler
async def get_is_student_in_group_on_discipline(request) -> Response:
    serializer = StudentAlreadyStudyingOnDisciplineSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(await is_student_in_group_on_discipline(
        student_id=serializer.validated_data.get('student_id'),
        discipline=serializer.validated_data.get('discipline')
    ), status=status.HTTP_200_OK)


@acontroller('Отправка сообщения клиента в amo, что группы не подошли', True)
@api_view(('POST',))
@asemaphore_handler
async def send_nothing_fit(request) -> Response:
    serializer = SendNothingFitSerializer(data=request.POST)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(await send_nothing_fit_units_to_amo(
        student_id=serializer.validated_data['student_id'],
        msg=serializer.validated_data['msg']
    ), status=status.HTTP_200_OK)


@acontroller('Сгенерировать ссылку для триггера amo на подбор группы ВМ', True)
@api_view(('GET',))
@asemaphore_handler
async def build_link_for_join_to_forming_group(request) -> HttpResponse:
    serializer = BuildLinkForJoinToFormingGroupSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return HttpResponse(
        (await create_short_link(
            f'http{"s" if settings.HTTPS else ""}://'
            f'{settings.MAIN_DOMAIN}{":8000" if settings.DEBUG else ""}'
            f'{reverse("tools:join_to_forming_group")}?'
            f'level={quote(serializer.validated_data["level"])}&'
            f'discipline={quote(serializer.validated_data["discipline"])}&'
            f'age={serializer.validated_data["age"]}&'
            f'student_id={serializer.validated_data["student_id"]}'
        )).get_short_url(),
        content_type="text/plain")
