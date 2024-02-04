import logging

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

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


# @controller('Получение групп для записи на вводный модуль.', True)
@api_view(('GET',))
# @semaphore_handler
def get_forming_groups_for_join(request) -> Response:
    serializer = FormingGroupParamsSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    from tools.services.signup_group.funcs import get_forming_groups_for_join
    get_forming_groups_for_join_sync = async_to_sync(get_forming_groups_for_join)
    return Response(get_forming_groups_for_join_sync(
        level=serializer.validated_data['level'],
        discipline=serializer.validated_data['discipline'],
        age=serializer.validated_data['age'],
    ), status=status.HTTP_200_OK)


# @controller('Добавление ученика на вводный модуль', True)
@api_view(('POST',))
# @semaphore_handler
def student_to_forming_group(request) -> Response:
    serializer = StudentToGroupSerializer(data=request.POST)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    result: bool = async_to_sync(add_student_to_forming_group)(
        student_id=serializer.validated_data.get('student_id'),
        group_id=serializer.validated_data.get('group_id')
    )
    return Response(data={'success': result},
                    status=status.HTTP_200_OK if result
                    else status.HTTP_400_BAD_REQUEST)


# @controller('Проверка записан ли уже ученик', True)
@api_view(('GET',))
# @semaphore_handler
def get_is_student_in_group_on_discipline(request) -> Response:
    serializer = StudentAlreadyStudyingOnDisciplineSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    result = async_to_sync(is_student_in_group_on_discipline)(
        student_id=serializer.validated_data.get('student_id'),
        discipline=serializer.validated_data.get('discipline')
    )
    return Response(result, status=status.HTTP_200_OK)


