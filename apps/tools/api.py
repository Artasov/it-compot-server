import logging
from datetime import datetime, timedelta
from urllib.parse import quote

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.Core.services.base import asemaphore_handler, acontroller
from apps.link_shorter.services.common import create_short_link
from apps.tools.exeptions.common import UnitAlreadyFullException
from apps.tools.serializers import (
    StudentAlreadyStudyingOnDisciplineSerializer,
    FormingGroupParamsSerializer,
    StudentToGroupSerializer,
    SendNothingFitSerializer,
    BuildLinkForJoinToFormingGroupSerializer, AddHhPaymentByAmoSerializer,
)
from apps.tools.services.other import get_course_themes
from apps.tools.services.signup_group.funcs import (
    is_student_in_group_on_discipline,
    add_student_to_forming_group, send_nothing_fit_units_to_amo
)
from service.common.common import calculate_age
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager, SetCommentError

log = logging.getLogger('base')


@acontroller('Отправка отчета по занятию.', auth=True)
@asemaphore_handler
async def send_lesson_report(request):
    ed_unit_id = request.POST.get('ed_unit_id')
    day_date = request.POST.get('day_date')
    theme_number = request.POST.get('theme_number')
    theme_name = request.POST.get('theme_name')
    lesson_completion_percentage = request.POST.get('lesson_completion_percentage')
    additional_info = request.POST.get('additional_info')
    if not all((ed_unit_id, day_date, theme_number, theme_name, lesson_completion_percentage)):
        return JsonResponse({'error': 'Неверные данные для отправки отчета.'}, 400)

    HHManager = CustomHHApiV2Manager()
    try:
        await HHManager.set_comment_for_all_students_ed_unit(
            ed_unit_id=ed_unit_id,
            date=day_date,
            description=f'* {theme_number}. {theme_name}\n'
                        f'* Завершено на: {lesson_completion_percentage}%\n'
                        f'* {additional_info}'
        )
    except SetCommentError:
        return JsonResponse({'error': 'Ошибка при добавлении комментария в HH'}, 400)
    return JsonResponse({'success': True})


@acontroller('Получение учебных единиц для отчета по занятию.', auth=True)
@asemaphore_handler
async def get_course_themes_view(request):
    return JsonResponse({
        'themes': await get_course_themes(request.GET['discipline'])
    })


# adrf неверно использует аутентификацию и пользователь всегда анонимный
@acontroller('Получение учебных единиц для отчета по уроку.', auth=True)
@asemaphore_handler
async def get_teacher_lesson_for_report(request) -> JsonResponse:
    HHManager = CustomHHApiV2Manager()
    now = datetime.now()
    email = request.user.email
    teacher = await HHManager.get_teacher_by_email(email=email)
    units = await HHManager.get_ed_units_in_daterange(
        start_date=now - timedelta(days=settings.ALLOWED_DAYS_FOR_LESSON_REPORT),
        end_date=now,
        types='Group,MiniGroup,Individual',
        queryDays=True,
        statuses='Forming',
        teacherId=teacher['Id']
    )
    res = []
    for unit in units:
        if 'EVENTS' not in unit['Name']:
            res.append(unit)
    return JsonResponse({'units': res})


@acontroller('Получение групп для записи на вводный модуль.')
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
            client_tz=serializer.validated_data.get('client_tz')
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
