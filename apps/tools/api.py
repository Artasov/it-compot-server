import json
import logging
from datetime import datetime, timedelta
from urllib.parse import quote

from adrf.decorators import api_view
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from apps.Core.services.base import asemaphore_handler, acontroller
from apps.link_shorter.services.common import create_short_link
from apps.tools.exceptions.common import UnitAlreadyFullException
from apps.tools.serializers import (
    StudentAlreadyStudyingOnDisciplineSerializer,
    FormingGroupParamsSerializer,
    StudentToGroupSerializer,
    SendNothingFitSerializer,
    BuildLinkForJoinToFormingGroupSerializer, AddHhPaymentByAmoSerializer,
)
from apps.tools.services.lesson_report import send_gs_lesson_report
from apps.tools.services.other import get_course_themes
from apps.tools.services.signup_group.funcs import (
    is_student_in_group_on_discipline,
    add_student_to_forming_group, send_nothing_fit_units_to_amo
)
from service.common.common import calculate_age
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager, SetCommentError

log = logging.getLogger('base')

JsonResponse
@acontroller('Отправка отчета по занятию.', auth=True)
@asemaphore_handler
async def send_lesson_report(request):
    ed_unit_id = request.POST.get('ed_unit_id')
    day_date = request.POST.get('day_date')
    theme_number = request.POST.get('theme_number')
    theme_name = request.POST.get('theme_name')
    lesson_completion_percentage = request.POST.get('lesson_completion_percentage')
    students_comments = request.POST.get('students_comments')
    type_ed_unit = request.POST.get('type')
    if not all((ed_unit_id, day_date, theme_name, lesson_completion_percentage)):
        return JsonResponse({'success': False, 'error': 'Неверные данные для отправки отчета.'}, 400)

    try:
        students_comments = json.loads(students_comments)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных студентов.'}, 400)

    HHManager = CustomHHApiV2Manager()
    teacher_name = await HHManager.get_full_teacher_name_by_email(request.user.email)
    for student_comment in students_comments:
        try:
            await HHManager.set_comment_for_student_ed_unit(
                ed_unit_id=ed_unit_id,
                student_client_id=student_comment['ClientId'],
                date=day_date,
                description=f'* {theme_number}{". " if theme_number else ""}{theme_name}\n'
                            f'* Завершено на: {lesson_completion_percentage}%\n'
                            f'* {student_comment["Description"]}'
            )
            await send_gs_lesson_report(
                teacher_name=teacher_name,
                type_ed_unit=type_ed_unit,
                ed_unit_id=ed_unit_id,
                student_name=student_comment['StudentName'],
                student_client_id=student_comment['ClientId'],
                date=day_date,
                description=f'* {theme_number}. {theme_name}\n'
                            f'* Завершено на: {lesson_completion_percentage}%\n'
                            f'* {student_comment["Description"]}'
            )
        except SetCommentError:
            return JsonResponse({
                'success': False,
                'error': 'Ошибка при добавлении комментария в HH'
            }, 400)

    return JsonResponse({'success': True})


@acontroller('Получение тем курса по его названию', auth=True)
@asemaphore_handler
async def get_course_themes_view(request):
    return JsonResponse({
        'themes': await get_course_themes(request.GET['discipline'])
    })


# adrf неверно использует аутентификацию и пользователь всегда анонимный
@acontroller('Получение учебных единиц для отчета по уроку', auth=True)
@asemaphore_handler
async def get_teacher_lesson_for_report(request) -> JsonResponse:
    HHManager = CustomHHApiV2Manager()
    now = datetime.now()
    email = request.user.email
    teacher = await HHManager.get_teacher_by_email(email=email)
    units = await HHManager.get_ed_units_with_filtered_days_in_daterange(
        start_date=now - timedelta(days=settings.ALLOWED_DAYS_FOR_LESSON_REPORT),
        end_date=now,
        types='Group,MiniGroup,Individual',
        statuses='Forming',
        teacherId=teacher['Id']
    )
    # Убираем школьные события
    filtered_units = []
    for unit in units:
        if 'EVENTS' not in unit['Name']:
            filtered_units.append(unit)
    # Добавляем информацию по ученикам с днями для каждой учебной единицы
    for i in range(0, len(filtered_units)):
        unit_students = await HHManager.getEdUnitStudents(
            edUnitId=filtered_units[i]['Id'],
            queryDays=True,
            dateFrom=(now - timedelta(days=settings.ALLOWED_DAYS_FOR_LESSON_REPORT)).strftime('%Y-%m-%d'),
            dateTo=now.strftime('%Y-%m-%d'),
        )
        filtered_units[i]['Students'] = unit_students
    return JsonResponse({'units': filtered_units})


@acontroller('Получение групп для авто-записи')
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
            datetime.fromtimestamp(age_or_tsmp_birth).strftime('%Y-%m-%d')
        ) if age_or_tsmp_birth > 100 else age_or_tsmp_birth,
    ), status=status.HTTP_200_OK)


@acontroller('Добавление ученика на вводный модуль')
@api_view(('POST',))
@asemaphore_handler
async def student_to_forming_group(request) -> Response:
    serializer = StudentToGroupSerializer(data=request.POST)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        await add_student_to_forming_group(
            student_id=serializer.validated_data.get('student_id'),
            group_id=serializer.validated_data.get('group_id'),
            client_tz=serializer.validated_data.get('client_tz'),
            join_type=serializer.validated_data.get('join_type')
        )
    except UnitAlreadyFullException:
        return Response(data={
            'success': False,
            'error': 'Обновите страницу.'
        }, status=status.HTTP_409_CONFLICT)

    return Response(data={'success': True}, status=status.HTTP_200_OK)


@acontroller('Проверка записан ли уже ученик')
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


@acontroller('Отправка сообщения клиента в amo, что группы не подошли')
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


@acontroller('Сгенерировать ссылку для триггера amo на подбор группы ВМ')
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


@acontroller('Добавление платежа в hh по тригеру из amo')
@api_view(('POST',))
@asemaphore_handler
async def add_hh_payment_by_amo_view(request) -> Response:
    serializer = AddHhPaymentByAmoSerializer(data=request.POST)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = await serializer.adata

    log.critical(f'{data=}')
    student_id = data.get('student_id')
    currency = data.get('currency')
    if currency == '': currency = 'Рубль'
    summ = data.get('sum')
    payment_type = data.get('payment_type')
    course = data.get('course')

    log.critical('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    log.critical(student_id)
    log.critical(currency)
    log.critical(summ)
    log.critical(payment_type)
    log.critical(course)
    log.critical('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')

    result = await CustomHHApiV2Manager().add_hh_payment_by_amo(
        student_amo_id=student_id,
        amo_currency=currency,
        summ=summ,
        amo_payment_type=payment_type,
        course=course
    )

    return Response(data=result, status=status.HTTP_200_OK)
