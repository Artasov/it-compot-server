import logging

from adrf.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from Core.services.common import acontroller, semaphore_handler
from tools.serializers import (
    StudentAlreadyStudyingOnDisciplineSerializer,
    FormingGroupParamsSerializer,
    StudentToGroupSerializer,
)
from tools.services.signup_group.funcs import (
    is_student_in_group_on_discipline,
    add_student_to_forming_group
)

log = logging.getLogger('base')


@acontroller('Получение групп для записи на вводный модуль.', True)
@semaphore_handler
@api_view(('GET',))
async def get_forming_groups_for_join(request) -> Response:
    serializer = FormingGroupParamsSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    from tools.services.signup_group.funcs import get_forming_groups_for_join
    return Response(
        data=await get_forming_groups_for_join(
            level=serializer.validated_data.get('level'),
            discipline=serializer.validated_data.get('discipline'),
            age=serializer.validated_data.get('age'),
        ), status=status.HTTP_200_OK
    )


@acontroller('Добавление ученика на вводный модуль', True)
@semaphore_handler
@api_view(('POST',))
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
@semaphore_handler
@api_view(('GET',))
async def get_is_student_in_group_on_discipline(request) -> Response:
    serializer = StudentAlreadyStudyingOnDisciplineSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        data=await is_student_in_group_on_discipline(
            student_id=serializer.validated_data.get('student_id'),
            discipline=serializer.validated_data.get('discipline')
        ), status=status.HTTP_200_OK)
