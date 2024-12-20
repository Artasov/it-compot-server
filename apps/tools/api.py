import asyncio
import json
import logging
from datetime import datetime, timedelta
from pprint import pprint
from time import sleep
from urllib.parse import quote

from adrf.decorators import api_view
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, Http404
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT

from apps.Core.services.base import asemaphore_handler, acontroller, controller
from apps.link_shorter.services.common import create_short_link
from apps.tools.exceptions.common import UnitAlreadyFullException
from apps.tools.serializers import (
    StudentAlreadyStudyingOnDisciplineSerializer,
    FormingGroupParamsSerializer,
    StudentToGroupSerializer,
    SendNothingFitSerializer,
    BuildLinkForJoinToFormingGroupSerializer, AddHhPaymentByAmoSerializer,
)
from apps.tools.services.lesson_report.funcs import parse_lesson_comment, LessonComment, \
    get_module_for_autumn_by_lesson_number, get_module_by_lesson_number
from apps.tools.services.other import get_course_themes
from apps.tools.services.signup_group.funcs import (
    add_student_to_forming_group, send_nothing_fit_units_to_amo, get_forming_groups_for_join
)
from apps.tools.tasks.tasks import process_lesson_report_task
from modules.common.common import calculate_age, get_number, now_date
from modules.gsheet.classes.gsheetsclient import GSDocument, GSFormatOptionVariant
from modules.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from modules.hollihop.classes.custom_hollihop_sync import CustomHHApiV2SyncManager
from modules.hollihop.consts import base_ages, get_next_discipline
from modules.pickler import Pickler, PicklerNotFoundDumpFile, PicklerLoadError

log = logging.getLogger('base')
pickler = Pickler(**settings.PICKLER_SETTINGS)


@acontroller('Отправка отчета по занятию.')
@asemaphore_handler
@permission_classes((IsAuthenticated,))
@api_view(('POST',))
async def send_lesson_report(request):
    ed_unit_id = request.data.get('ed_unit_id')
    day_date = request.data.get('day_date')
    theme_number = request.data.get('theme_number')
    theme_name = request.data.get('theme_name')
    lesson_completion_percentage = request.data.get('lesson_completion_percentage')
    students_comments = request.data.get('students_comments')
    type_ed_unit = request.data.get('type')
    growth_points = request.data.get('growth_points')
    what_was_positive = request.data.get('what_was_positive')
    satisfaction_rate = request.data.get('satisfaction_rate')
    self_feeling_rate = request.data.get('self_feeling_rate')
    students_feeling_rate = request.data.get('students_feeling_rate')
    other_general_questions = request.data.get('other_general_questions')

    if not all((ed_unit_id, day_date, theme_name,
                lesson_completion_percentage, growth_points,
                what_was_positive, satisfaction_rate, self_feeling_rate,
                students_feeling_rate)):
        return Response({'success': False, 'error': 'Неверные данные для отправки отчета.'}, 400)
    try:
        students_comments = json.loads(students_comments)
    except json.JSONDecodeError:
        return Response({'success': False, 'error': 'Неверный формат данных студентов.'}, 400)
    pickler.delete(f'{request.user.username}_lessons')
    cache.delete(f'{request.user.username}_lessons')
    process_lesson_report_task.delay(
        ed_unit_id=ed_unit_id,
        day_date=day_date,
        theme_number=theme_number,
        theme_name=theme_name,
        lesson_completion_percentage=lesson_completion_percentage,
        students_comments=students_comments,
        type_ed_unit=type_ed_unit,
        user_email=request.user.email,
        growth_points=growth_points,
        what_was_positive=what_was_positive,
        satisfaction_rate=satisfaction_rate,
        self_feeling_rate=self_feeling_rate,
        students_feeling_rate=students_feeling_rate,
        other_general_questions=other_general_questions,
    )

    return Response({'success': True}, 200)


@acontroller('Получение тем курса по его названию', auth=True)
@asemaphore_handler
@api_view(('GET',))
async def get_course_themes_view(request):
    discipline = request.GET['discipline']
    try:
        themes = pickler.cache(f'{discipline}_{now_date()}')
    except (PicklerNotFoundDumpFile, PicklerLoadError) as e:
        print(e)
        themes = await get_course_themes(discipline)
        pickler.cache(f'{discipline}_{now_date()}', obj=themes)
    return Response({'themes': themes}, 200)


@acontroller('Получение учебных единиц для отчета по уроку', auth=True)
@asemaphore_handler
@api_view(('GET', 'POST'))
@permission_classes((IsAuthenticated,))
async def get_teacher_lesson_for_report(request) -> Response:
    start_time = datetime.now()  # ЗАМЕР
    filtered_units = cache.get(f'{request.user.username}_lessons', None)
    if filtered_units is not None: return Response({'units': filtered_units}, 200)

    email = request.user.email
    HHManager = CustomHHApiV2Manager()
    now = datetime.now()
    teacher = await HHManager.get_teacher_by_email(email=email)
    if not teacher: raise Http404('Учитель не найден')
    units = await HHManager.get_ed_units_with_filtered_days_in_daterange(
        start_date=now - timedelta(days=settings.ALLOWED_DAYS_FOR_LESSON_REPORT),
        end_date=now,
        types='Group,MiniGroup,Individual',
        statuses='Forming',
        teacherId=teacher['Id'],
        maxTake=1000,
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
            maxTake=100,
            dateFrom=(now - timedelta(days=settings.ALLOWED_DAYS_FOR_LESSON_REPORT)).strftime('%Y-%m-%d'),
            dateTo=now.strftime('%Y-%m-%d'),
        )
        filtered_units[i]['Students'] = unit_students
    if len(filtered_units): cache.set(f'{request.user.username}_lessons', filtered_units, timeout=60 * 60)
    end_time = datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()
    print(f"!!! Lessons {request.user.email} GET BY: {elapsed_time} seconds")

    return Response({'units': filtered_units}, 200)


@acontroller('Получение групп для авто-записи')
@api_view(('GET',))
@asemaphore_handler
async def forming_groups_for_join(request) -> Response:
    # В age можно передавать timestamp даты рождения или сразу возраст
    serializer = FormingGroupParamsSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    # Получаем параметры если они есть
    if all((data.get('age'), data.get('level'), data.get('discipline'))):
        discipline = data['discipline']
        age = calculate_age(
            datetime.fromtimestamp(data['age']).strftime('%Y-%m-%d')
        ) if data['age'] > 100 else data['age']
        level = data['level']
        return Response(await get_forming_groups_for_join(
            level=level,
            discipline=discipline,
            age=age,
            learningTypes='Вводный модуль курса (russian language)',
        ), status=HTTP_200_OK)

    # Узнаем параметры по данным ученика если они есть
    elif any((data.get('student_full_name'), data.get('email'), data.get('tel'))) and data.get('discipline'):
        discipline = data['discipline']
        HHM = CustomHHApiV2Manager()

        student = await HHM.get_student_by_fio_or_email_or_tel(
            data.get('student_full_name'), data.get('email'), data.get('tel')
        )
        if not student:
            return Response({'success': False, 'error': 'Не найдено ученика по указанным данным.'}, 404)
        if await HHM.is_student_in_group_on_discipline(
                student_amo_id=HHM.get_student_or_student_unit_extra_field_value(student, 'id ученика'),
                discipline=discipline):
            return Response({'success': False, 'error': 'Ученик уже есть в группе по данной дисциплине.'}, 409)

        last_ed_unit_s = await HHM.get_latest_ed_unit_s_for_student_on_discipline(student['ClientId'], discipline)
        # pprint('last_ed_unit_s')
        # pprint(last_ed_unit_s)
        if not last_ed_unit_s:
            return Response({'success': False, 'error': 'Не найдена предыдущая группа по данной дисциплине.'}, 404)
        level = last_ed_unit_s['EdUnitLevel']
        pprint(f'{level=}')
        age = calculate_age(student['Birthday']) if student.get('Birthday') else base_ages.get(f'{discipline} {level}')
        if not age:
            return Response({'success': False, 'error': 'Возраст не определен.'}, 409)
        pprint(f'{age=}')
        last_comment: LessonComment = parse_lesson_comment(HHM.get_last_day_desc(last_ed_unit_s))
        if not last_comment:
            return Response({'success': False,
                             'error': 'Не найден последний комментарий ученика по данной дисциплине, либо формат комментария неверный.'},
                            404)
        pprint('last_comment')
        pprint(last_comment)
        if not last_comment['finish_percent']:
            last_comment['finish_percent'] = 100
        module_for_join = get_module_for_autumn_by_lesson_number(
            last_comment['number'] if last_comment['finish_percent'] > 50 else (
                last_comment["number"] - 1 if last_comment['number'] > 1 else last_comment['number']), discipline)
        pprint(f'{module_for_join=}')
        if module_for_join == 'Переход':
            module_for_join = get_module_by_lesson_number(
                lesson_number=1,
                discipline=get_next_discipline(
                    age=age, discipline=discipline, level=level
                ))
        ed_units = await get_forming_groups_for_join(
            level=level,
            discipline=discipline,
            age=age,
            learningTypes='Занятия в микро-группах (russian language)',
            extraFieldName='Стартовый модуль',
            extraFieldValue=module_for_join,
            join_type='autumn',
        )
        pprint(len(ed_units))
        ed_units['student_id'] = HHM.get_student_or_student_unit_extra_field_value(student, 'id ученика')
        return Response(ed_units, status=HTTP_200_OK)

    else:
        return Response({'success': False, 'error': 'Неверное количество или значения параметров GET запроса.'}, 400)


@acontroller('Добавление ученика на вводный модуль')
@api_view(('POST',))
@asemaphore_handler
async def student_to_forming_group(request) -> Response:
    serializer = StudentToGroupSerializer(data=request.POST)
    if not serializer.is_valid():
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
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
        }, status=HTTP_409_CONFLICT)

    return Response(data={'success': True}, status=status.HTTP_200_OK)


@acontroller('Проверка записан ли уже ученик')
@api_view(('GET',))
@asemaphore_handler
async def get_is_student_in_group_on_discipline(request) -> Response:
    serializer = StudentAlreadyStudyingOnDisciplineSerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    HHM = CustomHHApiV2Manager()
    return Response(await HHM.is_student_in_group_on_discipline(
        student_amo_id=serializer.validated_data.get('student_id'),
        discipline=serializer.validated_data.get('discipline')
    ), status=status.HTTP_200_OK)


@acontroller('Отправка сообщения клиента в amo, что группы не подошли')
@api_view(('POST',))
@asemaphore_handler
async def send_nothing_fit(request) -> Response:
    serializer = SendNothingFitSerializer(data=request.POST)
    if not serializer.is_valid(): return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(await send_nothing_fit_units_to_amo(
        student_id=serializer.validated_data['student_id'],
        msg=serializer.validated_data['msg'],
        join_type=serializer.validated_data['join_type'],
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


@acontroller('Выгрузка средней цены урока для каждого ученика')
@api_view(('GET',))
async def upload_average_price_per_lesson_student(request) -> Response:
    pickler = Pickler(settings.BASE_CACHE_DIR)
    HHM = CustomHHApiV2Manager()
    try:
        ed_units_s = pickler.cache('upload_average_price_per_lesson/ed_units_s')
    except (PicklerNotFoundDumpFile, PicklerLoadError):
        ed_units_s = await HHM.getEdUnitStudents(maxTake=6000, queryDays=True, dateFrom='2024-05-01',
                                                 dateTo='2024-07-01')
        pickler.cache('upload_average_price_per_lesson/ed_units_s', ed_units_s)

    # pprint(ed_units_s)
    ed_units_s = HHM.filter_ed_units_with_any_days_later_than_date(ed_units_s,
                                                                   datetime.strptime('2024-05-01', '%Y-%m-%d'))
    ed_units_s = HHM.filter_latest_ed_unit_s_for_student_on_disciplines(ed_units_s)
    print('len(ed_units_s)')
    print(len(ed_units_s))

    try:
        students = pickler.cache('upload_average_price_per_lesson/students')
    except (PicklerNotFoundDumpFile, PicklerLoadError):
        students = []

        async def fetch_student(sunit):
            retry_attempts = 30
            for attempt in range(retry_attempts):
                try:
                    student_ = (await HHM.getStudents(maxTake=1, clientId=sunit['StudentClientId']))[0]
                    return {
                        'Id': student_['Id'],
                        'id ученика': HHM.get_student_or_student_unit_extra_field_value(student_, 'id ученика'),
                        'ClientId': student_['ClientId'],
                        'StudentName': sunit['StudentName']
                    }
                except Exception:
                    if attempt < retry_attempts - 1:
                        await asyncio.sleep(attempt * retry_attempts)  # Ждем 1 секунду перед повторной попыткой
                    else:
                        raise

        batch_size = 500

        for i in range(0, len(ed_units_s), batch_size):
            batch = ed_units_s[i:i + batch_size]
            students_batch = await asyncio.gather(*(fetch_student(sunit) for sunit in batch))
            students.extend(students_batch)
            print(f"Processed batch {i // batch_size + 1}")
            if i + batch_size < len(ed_units_s):
                await asyncio.sleep(31)
        students = pickler.cache('upload_average_price_per_lesson/students', students)
    print(len(students))

    try:
        result = pickler.cache('upload_average_price_per_lesson/result')
    except (PicklerNotFoundDumpFile, PicklerLoadError):
        result = []
        batch_size = 500
        total_students = len(students)
        for i in range(0, total_students, batch_size):
            batch_students = students[i:i + batch_size]
            for student in batch_students:
                print(f"Processing student {i + batch_students.index(student) + 1} out of {total_students}")
                i_and_o = None
                retries = 15
                for attempt in range(retries):
                    try:
                        i_and_o = await HHM.getIncomesAndOutgoes(clientId=student['ClientId'])
                        break
                    except Exception as e:
                        if attempt < retries - 1:
                            await asyncio.sleep(240)
                        else:
                            raise e

                if i_and_o:
                    student_items = i_and_o['Study']['Items']
                    ed_unit_prices = {}
                    for item in student_items:
                        if not item.get('EdUnitName'):
                            continue
                        if item['Type'] != 'Study':
                            continue

                        ed_unit_id = item['EdUnitId']

                        exist_unit = False
                        for ed_units_s_ in ed_units_s:
                            if (ed_units_s_['EdUnitId'] == ed_unit_id
                                    and ed_units_s_['StudentClientId'] == student['ClientId']):
                                exist_unit = True
                        if not exist_unit:
                            print('Пропуск')
                            continue

                        value_str = item['Value']
                        try:
                            if 'руб.' in value_str:
                                value = float(get_number(value_str))
                            elif 'тг.' in value_str:
                                value = float(get_number(value_str)) * 0.1989
                            elif '$' in value_str:
                                value = float(get_number(value_str)) * 88.99
                            elif '€' in value_str:
                                value = float(get_number(value_str)) * 95.64
                            elif '£' in value_str:  # британский фунт
                                value = float(get_number(value_str)) * 113.24
                            elif '?' in value_str:
                                continue
                            else:
                                print(value_str)
                                raise TypeError('ВАЛЮТА НЕ РАСПОЗНАНА')
                        except TypeError as e:
                            raise e
                        except Exception as e:
                            print(value_str)
                            raise e

                        if ed_unit_id not in ed_unit_prices:
                            ed_unit_prices[ed_unit_id] = {'total_value': 0, 'total_items': 0,
                                                          'ed_unit_name': item['EdUnitName']}

                        ed_unit_prices[ed_unit_id]['total_value'] += value
                        ed_unit_prices[ed_unit_id]['total_items'] += 1
                        if int(student['Id']) == 24932:
                            pprint(i_and_o)
                            pprint(ed_unit_prices)
                            raise Exception('СМОТРИ')

                    for ed_unit_id, data in ed_unit_prices.items():
                        avg_price = round(data['total_value'] / data['total_items'], 2) if data[
                                                                                               'total_items'] > 0 else 0
                        result.append((
                            student['StudentName'],
                            student['Id'],
                            student['id ученика'],
                            data['ed_unit_name'],
                            ed_unit_id,
                            avg_price
                        ))

            if i + batch_size < total_students:
                print('Sleeping for 31 seconds')
                await asyncio.sleep(31)
        result = pickler.cache('upload_average_price_per_lesson/result', result)

    GSDocument(settings.GSDOCID_UPLOAD_AVERAGE_PRICE_PER_LESSON_STUDENT[0]).update_sheet_with_format_header(
        sheet_name=settings.GSDOCID_UPLOAD_AVERAGE_PRICE_PER_LESSON_STUDENT[1],
        header=(
            'StudentName',
            'StudentId',
            'StudentAmoId',
            'EdUnitName',
            'EdUnitId',
            'Average lesson price (RUB)',
        ),
        values=result,
        format_header=GSFormatOptionVariant.BASE_HEADER
    )

    return Response(data={'result': result}, status=HTTP_200_OK)


async def upload_days_with_wrong_comment(request) -> Response:
    HHM = CustomHHApiV2Manager()
    try:
        ed_units_s = pickler.cache('upload_days_with_wrong_comment/ed_units_s')
    except (PicklerNotFoundDumpFile, PicklerLoadError):
        ed_units_s = await HHM.getEdUnitStudents(maxTake=6000, queryDays=True, dateFrom='2024-05-01',
                                                 dateTo='2024-07-01')
        pickler.cache('upload_days_with_wrong_comment/ed_units_s', ed_units_s)

    # pprint(ed_units_s)
    ed_units_s = HHM.filter_ed_units_with_any_days_later_than_date(
        ed_units_s, datetime.strptime('2024-05-01', '%Y-%m-%d')
    )
    ed_units_s = [HHM.filter_ed_unit_days_by_daterange(
        ed_unit_s,
        datetime.strptime('2024-05-01', '%Y-%m-%d'),
        datetime.strptime('2024-06-02', '%Y-%m-%d')
    ) for ed_unit_s in ed_units_s]

    # pickler.cache(f'upload_days_with_wrong_comment/backups/ed_units_s.{datetime.now().strftime("%Y-%m-%d")}.{random.randint(10000, 100000)}')

    wrong_days = []
    latest_wrong_days = {}
    for ed_unit_s in ed_units_s:
        for day in ed_unit_s.get('Days', []):
            if day.get('Pass') is False:
                ed_unit_id = ed_unit_s['EdUnitId']
                day_date = datetime.strptime(day['Date'], '%Y-%m-%d')
                if ed_unit_id not in latest_wrong_days or day_date > latest_wrong_days[ed_unit_id]['DayDate']:
                    if day.get('Description', '').count('*') != 3:
                        latest_wrong_days[ed_unit_id] = {
                            'StudentClientId': ed_unit_s['StudentClientId'],
                            'EdUnitId': ed_unit_s['EdUnitId'],
                            'Discipline': ed_unit_s['EdUnitDiscipline'],
                            'DayDate': day_date,
                            'Pass': day.get('Pass'),
                            'WrongDescription': day.get('Description')
                        }
    # Преобразование дат обратно в строковый формат и создание итогового списка
    wrong_days = [
        {
            'StudentClientId': value['StudentClientId'],
            'EdUnitId': value['EdUnitId'],
            'Discipline': value['Discipline'],
            'DayDate': value['DayDate'].strftime('%Y-%m-%d'),
            'Pass': value['Pass'],
            'WrongDescription': value['WrongDescription']
        }
        for value in latest_wrong_days.values()
    ]
    pprint(wrong_days)
    print('len(wrong_days)')
    pprint(len(wrong_days))
    # try:
    #     await HHManager.set_comment_for_student_ed_unit(
    #         ed_unit_id=ed_unit_id,
    #         student_client_id=student_comment['ClientId'],
    #         date=day_date,
    #         passed=student_comment['Pass'],
    #         description=f'* {theme_number}{". " if theme_number else ""}{theme_name}\n'
    #                     f'* Завершено на: {lesson_completion_percentage}%\n'
    #                     f'* {student_comment["Description"]}'
    #     )
    # except SetCommentError:
    #     return JsonResponse({
    #         'success': False,
    #         'error': 'Ошибка при добавлении комментария в HH'
    #     }, 400)
    print('len(ed_units_s)')
    print(len(ed_units_s))
    result = []
    for day in wrong_days:
        result.append((
            day['StudentClientId'],
            day['EdUnitId'],
            day['Discipline'],
            day['DayDate'],
            day['Pass'],
            day['WrongDescription'],
        ))
    GSDocument(settings.GSDOCID_UPLOAD_BY_LESSON).update_sheet_with_format_header(
        sheet_name='Wrong Comments',
        header=(
            'StudentClientId',
            'EdUnitId',
            'Discipline',
            'DayDate',
            'Pass',
            'WrongDescription',
        ),
        values=result,
        format_header=GSFormatOptionVariant.BASE_HEADER
    )


@controller('Загрузка откорректированных комментариев обратно в HH')
def reload_corrected_comments(request):
    doc = GSDocument(settings.GSDOCID_UPLOAD_BY_LESSON)
    comments = doc.get_sheet_as_list(sheet_name='Wrong Comments')[1:]
    HHM = CustomHHApiV2SyncManager()
    for i, comment in enumerate(comments):
        if '21536' == comment[1]:
            comments = comments[i:]
    for comment in comments:
        if len(comment) < 7:
            print(f'Skipped unit={int(comment[1])} student={int(comment[0])}')
            continue
        HHM.set_comment_for_student_ed_unit(
            ed_unit_id=int(comment[1]),
            student_client_id=int(comment[0]),
            date=comment[3],
            passed=False if comment[4] == 'FALSE' else True,
            description=comment[6]
        )
        sleep(0.35)
        print(f'Setted for unit={int(comment[1])} student={int(comment[0])}')
    return HttpResponse('OK')
# len(wrong_days)
# 13344
# len(ed_units_s)
# 5765
