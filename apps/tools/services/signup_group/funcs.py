import logging
from datetime import datetime, timedelta

import aiohttp
from django.conf import settings
from django.template.defaultfilters import pprint

from apps.tools.exceptions.common import UnitAlreadyFullException
from apps.tools.services.loggers.gsheet_logger import GSheetLoggerJoinFormingGroup as GLog
from service.common.common import calculate_age
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from service.hollihop.consts import amo_hh_disciplines_map
from service.tools.gsheet.classes.gsheetsclient import ColumnWidth

log = logging.getLogger('base')


def sort_groups_by_datetime(groups: list | tuple) -> list:
    """
    Сортирует по возрастанию даты переданный массив групп(EdUnits).
    @param groups: Массив из EdUnits
    @return: Отсортированный массив EdUnits
    """
    for group in groups:
        group['sort_key'] = datetime.strptime(
            group['ScheduleItems'][0]['BeginDate'] + ' ' + group['ScheduleItems'][0]['BeginTime'], "%Y-%m-%d %H:%M")
    sorted_groups = sorted(groups, key=lambda x: x['sort_key'])

    for group in sorted_groups:
        del group['sort_key']
    return sorted_groups


async def is_unit_vacant_for_join(unit: dict) -> bool:
    return True if unit['StudentsCount'] < unit['Vacancies'] else False


async def is_unit_suits_for_join(unit: dict, search_levels: list, age: int, discipline: str) -> bool:
    HHM = CustomHHApiV2Manager()
    # Получаем студентов группы
    edUnitsStudent = await HHM.get_ed_unit_students_by_unit_id([unit['Id']])
    students_client_ids = [int(unitS['StudentClientId']) for unitS in edUnitsStudent if
                           unitS['EdUnitId'] == unit['Id']]
    students_client_ids_set = set(students_client_ids)
    unique_student_ids = set()
    for unitS in edUnitsStudent:
        unique_student_ids.add(int(unitS['StudentClientId']))
    # Преобразуем set в tuple для запроса
    student_client_ids_tuple = tuple(set(unique_student_ids))
    # Получаем информацию по всем студентам одним запросом
    all_students_info = await HHM.get_students_by_client_ids(student_client_ids_tuple)
    # Преобразуем результат в словарь для удобства доступа
    students_info_dict = {student['ClientId']: student for student in all_students_info}

    # Если в группе еще пусто
    if not students_client_ids_set:
        return True
    # Используем предварительно полученную информацию о студентах
    students = [students_info_dict[student_id] for student_id in students_client_ids_set if
                student_id in students_info_dict]

    for student in students:
        # Если возраст отличается больше чем на 2 от запрошенного, то скип
        if age is not None:
            try:
                student_age = calculate_age(student['Birthday'])
                # print(student_age)
                if abs(student_age - age) > 2:
                    return False
            except KeyError:
                # print('Нет дня рождения')
                return False
        # Проверяем подходит ли по уровню
        if search_levels:
            try:  # Берем поле дисциплины:
                disciplines = student['Disciplines']
                for d in disciplines:
                    if d['Discipline'] == discipline:
                        if d['Level'] not in search_levels:
                            log.info(f'EdUnit {unit["Id"]}: Не подходит по уровню')
            except KeyError:
                # print('Нет Disciplines Discipline Level')
                return False
    return True


async def get_forming_groups_for_join(level: str,
                                      discipline: str,
                                      age: int,
                                      join_type: str = None,
                                      **kwargs
                                      ) -> dict:
    """
    @param level: Уровень ученика из списка amo_disciplines в consts.py
    @param discipline: Одно из направлений из списка в amo_levels consts.py
    @param age: Количество полных лет будущего ученика
    @param join_type: Стиль временной фильтрации
    @return: Словарь вида
    {
        'groups': Список с найденными группами по параметрам по api HolliHop,
        'join_type': 'academic_year' если сейчас НЕ лето, иначе summer
    }

    """
    HHM = CustomHHApiV2Manager()
    ed_units = await HHM.get_available_future_starting_ed_units(
        types='Group,MiniGroup',
        statuses='Forming',
        level=level,
        queryDays=True,
        discipline=discipline,
        age=age,
        **kwargs
    )

    now = datetime.now()
    # now = datetime(now.year, 5, 26)
    if not join_type:
        if datetime(now.year, 5, 26) <= now <= datetime(now.year, 8, 29):  # Если лето
            join_type = 'summer'
        elif datetime(now.year, 8, 30) <= now <= datetime(now.year, 11, 30):  # Если осень
            join_type = 'autumn'
        else:  # академический год
            join_type = 'academic_year'
    # print('UNITS')
    # print(ed_units)
    if join_type == 'summer':
        ed_units = HHM.filter_ed_units_with_days_later_than_date(
            units=ed_units, date=datetime(now.year, 6, 3))
        ed_units = HHM.filter_ed_units_where_first_day_earlier_than_date(
            units=ed_units, date=now + timedelta(days=7)
        )
    # elif join_type == 'autumn':
    #     ed_units = HHM.filter_ed_units_with_days_later_than_date(
    #         units=ed_units, date=datetime(now.year, 8, 30))
    elif join_type == 'autumn':
        ed_units = HHM.filter_ed_units_with_days_later_than_date(
            units=ed_units, date=now)
    elif join_type == 'academic_year':
        ed_units = HHM.filter_ed_units_with_days_earlier_than_date(
            units=ed_units, date=datetime(now.year, 6, 2))

    ed_units = sort_groups_by_datetime(ed_units)
    units_result = []
    for unit in ed_units:
        units_result.append({
            'Id': unit['Id'],
            'Type': unit['Type'],
            'Discipline': unit['Discipline'],
            'StudentsCount': unit['StudentsCount'],
            'Days': unit['Days'],
            'Vacancies': unit['Vacancies'],
            'ScheduleItems': unit['ScheduleItems'],
            'OfficeTimeZone': unit['OfficeTimeZone'],
        })
    return {
        'groups': units_result,
        'join_type': join_type
    }


async def add_student_to_forming_group(student_id: int, group_id: int, client_tz: int, join_type: str):
    """
    !!! ДЕКОМПОЗИРОВАТЬ !!!
    Добавляет студента в группу через amo api и логирует в googlesheets результат выполнения.
    @param student_id: Сквозной id ученика amo hh.
    @param group_id: EdUnit['Id'] идентификатор группы.
    @param client_tz: TZ клиента.
    @param join_type: строка 'summer' или 'academic_year' для верной записи в основной или летний период.
    @return: Если хоть что-то пойдет не так вернется False либо raise Error, иначе True.
    """
    HHManager = CustomHHApiV2Manager()
    column_widths = (
        ColumnWidth(column_index=1, width=170),
        ColumnWidth(column_index=2, width=250),
        ColumnWidth(column_index=3, width=280),
        ColumnWidth(column_index=4, width=155),
        ColumnWidth(column_index=5, width=250),
    )
    glog = GLog(doc_id=settings.GSDOCID_LOG_JOIN_FORMING_GROUPS,
                header=('Status', 'StudentAmoId', 'StudentHH', 'Groups', 'DateTime +0', 'Comment'),
                column_widths=column_widths)
    glog_autumn = GLog(doc_id=settings.GSDOCID_LOG_JOIN_FORMING_GROUPS_AUTUMN,
                       header=('Status', 'StudentAmoId', 'StudentHH', 'Groups', 'DateTime +0', 'Comment'),
                       column_widths=column_widths)
    student = await HHManager.get_student_by_amo_id(student_amo_id=student_id)

    # 1 ГРУППА
    forming_unit = (await HHManager.getEdUnits(
        id=group_id,
        queryDays=True,
        maxTake=1
    ))[0]
    if not is_unit_vacant_for_join(unit=forming_unit):
        raise UnitAlreadyFullException

    start_forming_unit_date_lesson1 = datetime.strptime(forming_unit['Days'][0]['Date'], '%Y-%m-%d')
    start_forming_unit_date_lesson2 = datetime.strptime(forming_unit['Days'][1]['Date'], '%Y-%m-%d') if len(
        forming_unit['Days']) > 1 else None
    pprint(forming_unit)
    print(start_forming_unit_date_lesson1)
    print(start_forming_unit_date_lesson2)
    start_forming_group_time = datetime.strptime(forming_unit['ScheduleItems'][0]['BeginTime'], '%H:%M')

    # pprint(forming_unit)

    result1 = await HHManager.addEdUnitStudent(
        edUnitId=group_id,
        studentClientId=student['ClientId'],
        comment=f'Добавлен(а) с помощью сайта в edUnits({group_id}).'
    )

    if len(forming_unit['ScheduleItems']) == 1:
        start_forming_unit_date2 = datetime.strptime(forming_unit['ScheduleItems'][0]['EndDate'], '%Y-%m-%d')
    elif len(forming_unit['ScheduleItems']) == 2:
        start_forming_unit_date2 = datetime.strptime(forming_unit['ScheduleItems'][1]['EndDate'], '%Y-%m-%d')
    else:
        start_forming_unit_date2 = 0
        glog.error(
            student_amo_id=student_id,
            student_hh_id=student['Id'],
            groups_ids=(f'{result1.get("success", False)}: {group_id}',),
            comment='Не нашел второй урок вводного модуля.'
        )

    if result1.get('success'):
        # Отправляем отчет в амо тригер чтобы проставились данные в сделку.
        datatime_start_moscow = datetime.combine(
            start_forming_unit_date_lesson1.date(),
            start_forming_group_time.time()
        )
        if start_forming_unit_date_lesson2 is not None:
            datatime_start2_moscow = datetime.combine(
                start_forming_unit_date_lesson2.date(),
                start_forming_group_time.time()
            )
        else:
            datatime_start2_moscow = None
        report_result = await send_report_join_to_forming_group(
            student_id=student_id,
            tel_number=student['Agents'][0]['Mobile'],
            discipline=next(
                (amo for amo, hh in amo_hh_disciplines_map if hh == forming_unit['Discipline']),
                "Дисциплина не найдена"),
            zoom_url=forming_unit['ScheduleItems'][0].get('ClassroomLink') if forming_unit['ScheduleItems'][0].get(
                'ClassroomLink') else 'NOT FOUND',
            teacher_id=forming_unit['ScheduleItems'][0]['TeacherId'],
            teacher_name=forming_unit['ScheduleItems'][0]['Teacher'],
            datetime_start_moscow=int(datatime_start_moscow.timestamp()),  # Дата и время старта ВМ
            datetime_start_client_tz=int((datatime_start_moscow + timedelta(hours=client_tz - 3)).timestamp()),
            datetime_first_summer_lesson_moscow=int(
                datatime_start_moscow.timestamp()) if datatime_start_moscow is not None else None,
            datetime_first_summer_lesson_client_tz=int(
                (datatime_start_moscow + timedelta(
                    hours=client_tz - 3)).timestamp()) if datatime_start_moscow is not None else None,
            datetime_second_summer_lesson_moscow=int(
                datatime_start2_moscow.timestamp()) if datatime_start2_moscow is not None else None,
            datetime_second_summer_lesson_client_tz=int((datatime_start2_moscow + timedelta(
                hours=client_tz - 3)).timestamp()) if datatime_start2_moscow is not None else None,
            date_end=int(start_forming_unit_date2.timestamp()) if start_forming_unit_date2 else 0,  # Дата окончания ВМ
            join_type=join_type
        )
        if not report_result:
            if join_type == 'autumn':
                glog_autumn.error(
                    student_amo_id=student_id,
                    student_hh_id=student['Id'],
                    groups_ids=(f'{result1.get("success", False)}: {group_id}',
                                f'{result1.get("success", False)}: '),
                    comment='Не смог отправить отчет в AMO'
                )
            else:

                glog.error(
                    student_amo_id=student_id,
                    student_hh_id=student['Id'],
                    groups_ids=(f'{result1.get("success", False)}: {group_id}',
                                f'{result1.get("success", False)}: '),
                    comment='Не смог отправить отчет в AMO'
                )
    if join_type == 'autumn':
        glog_autumn.success(
            student_amo_id=student_id,
            student_hh_id=student['Id'],
            groups_ids=(f'{result1.get("success", False)}: {group_id}',),
            comment='Записал'
        )
    else:
        glog.success(
            student_amo_id=student_id,
            student_hh_id=student['Id'],
            groups_ids=(f'{result1.get("success", False)}: {group_id}',),
            comment=f'Записал на вводный модуль {"(лето)" if join_type == "summer" else ""}'
        )

    # 2 ГРУППА
    result2 = False
    course_unit_id = False
    if join_type == 'academic_year' or join_type == 'autumn':
        if forming_unit.get('ExtraFields'):
            slot_code = next((field['Value'] for field in forming_unit['ExtraFields'] if field['Name'] == 'код-слот'),
                             None)
            course_unit_error = ''
            if not slot_code:
                course_unit_error = 'Не найдено поля код-слот'
            if str(slot_code)[-1] != '1':
                course_unit_error = 'Код-слот вводного модуля не равен 1.'
            # Если код-слот верный
            if not course_unit_error:
                course_unit = await HHManager.getEdUnits(
                    extraFieldName='код-слот',
                    extraFieldValue=str(slot_code)[:-1] + '2'
                )
                if len(course_unit) == 0:
                    course_unit_error = f'Не найдено группы с кодом {str(slot_code)[:-1] + "2"}.'
                elif len(course_unit) > 1:
                    course_unit_error = f'Найдено более 1ой группы с кодом {slot_code}.'
                course_unit_id = course_unit[0]['Id']
                if course_unit_error:
                    glog.error(
                        student_amo_id=student_id,
                        student_hh_id=student['Id'],
                        groups_ids=(f'{result1.get("success", False)}: {group_id}',),
                        comment=course_unit_error
                    )
                    await send_nothing_fit_units_to_amo(
                        student_id=student_id,
                        msg=course_unit_error,
                        func=1
                    )
                else:
                    result2 = await HHManager.addEdUnitStudent(
                        edUnitId=course_unit_id,
                        studentClientId=student['ClientId'],
                        comment=f'Добавлен(а) с помощью сайта в edUnits({group_id}, {course_unit[0]["Id"]}).'
                    )
                    if result2.get('success'):
                        glog.success(
                            student_amo_id=student_id,
                            student_hh_id=student['Id'],
                            groups_ids=(f'{result2.get("success", False)}: {course_unit_id}',),
                            comment='Записал в группу курса'
                        )
                    else:
                        await send_nothing_fit_units_to_amo(
                            student_id=student_id,
                            msg='Не смог записать в группу курса.',
                            func=1
                        )
                        glog.error(
                            student_amo_id=student_id,
                            student_hh_id=student['Id'],
                            groups_ids=(f'{result1.get("success", False)}: {group_id}',
                                        f'{result1.get("success", False)}: {course_unit[0]["Id"]}'),
                            comment=f'Не смог записать в группу курса.'
                        )
        # Если не найдены пользовательские поля которые нужны для обнаружения второй группы.
        else:
            glog.error(
                student_amo_id=student_id,
                student_hh_id=student['Id'],
                groups_ids=(f'{result1.get("success", False)}: {group_id}',),
                comment='Не найдено пользовательских полей у группы ВМ для обнаружения группы курса.'
            )
            await send_nothing_fit_units_to_amo(
                student_id=student_id,
                msg='Не найдено пользовательских полей у группы ВМ для обнаружения группы курса.',
                func=1
            )
    if result1.get("success"):
        # Открывает личный кабинет родителю
        groups_ids = [f'{result1.get("success", False)}: {group_id}']
        if result2:
            groups_ids.append(f'{result2.get("success", False)}: {course_unit_id}')

        open_personal_profile_result = await HHManager.setStudentAuthInfo(
            studentClientId=student['ClientId'],
            login=await HHManager.get_parent_email(student),
            password='2146648'
        )
        if not open_personal_profile_result.get('success'):
            if join_type == 'autumn':
                glog_autumn.error(
                    student_amo_id=student_id,
                    student_hh_id=student['Id'],
                    groups_ids=groups_ids,
                    comment='Не смог открыть личный кабинет'
                )
            else:
                glog.error(
                    student_amo_id=student_id,
                    student_hh_id=student['Id'],
                    groups_ids=groups_ids,
                    comment='Не смог открыть личный кабинет'
                )

        # Устанавливаем ссылку на amo в пользовательские поля
        result_add_amo_link = await HHManager.add_user_extra_field(
            student=student,
            field_name='Ссылка на amoCRM',
            field_value=f'https://itbestonlineschool.amocrm.ru/leads/detail/'
                        f'{next((field["Value"] for field in student["ExtraFields"] if field["Name"] == "id ученика"), None)}'
        )
        if not result_add_amo_link.get("success"):
            if join_type == 'autumn':
                glog_autumn.error(
                    student_amo_id=student_id,
                    student_hh_id=student['Id'],
                    groups_ids=groups_ids,
                    comment='Личный кабинет открыт, amo ссылка НЕ установлена'
                )
            else:
                glog.error(
                    student_amo_id=student_id,
                    student_hh_id=student['Id'],
                    groups_ids=groups_ids,
                    comment='Личный кабинет открыт, amo ссылка НЕ установлена'
                )
        if join_type == 'autumn':
            glog_autumn.error(
                student_amo_id=student_id,
                student_hh_id=student['Id'],
                groups_ids=groups_ids,
                comment='Личный кабинет открыт, amo ссылка НЕ установлена'
            )
        else:
            glog.success(
                student_amo_id=student_id,
                student_hh_id=student['Id'],
                groups_ids=groups_ids,
                comment='Личный кабинет открыт, amo ссылка установлена'
            )


def calc_base_age_by_level(level):
    pass


async def send_report_join_to_forming_group(
        student_id: int,
        tel_number: str,
        discipline: str,
        zoom_url: str,
        teacher_id: int,
        teacher_name: str,
        datetime_start_moscow: int,
        datetime_start_client_tz: int,
        datetime_first_summer_lesson_moscow: int,
        datetime_first_summer_lesson_client_tz: int,
        datetime_second_summer_lesson_moscow: int,
        datetime_second_summer_lesson_client_tz: int,
        join_type: str,
        date_end: int,
) -> bool:
    """
    Отправляет amo триггер информацию Post запросом о добавлении ученика.
    @param student_id: Сквозной id ученика amo hh
    @param tel_number: Телефон первого найденного агента у ученика
    @param discipline: Дисциплина
    @param zoom_url: Ссылка для подключения на занятие в зум
    @param teacher_id: id преподавателя группы
    @param teacher_name: Его имя
    @param datetime_start_moscow: timestamp Дата и время старта вводного модуля по москве
    @param datetime_start_client_tz: timestamp Дата и время старта вводного модуля по TZ клиента
    @param datetime_first_summer_lesson_moscow: timestamp Дата и время старта вводного модуля первого урока на лето по москве
    @param datetime_first_summer_lesson_client_tz: timestamp Дата и время старта вводного модуля первого урока на лето по TZ клиента
    @param datetime_second_summer_lesson_moscow: timestamp Дата и время старта вводного модуля второго урока на лето по москве
    @param datetime_second_summer_lesson_client_tz: timestamp Дата и время старта вводного модуля второго урока на лето по TZ клиента
    @param join_type:
    @param date_end: Дата окончания вводного модуля
    @return:
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=settings.AMOLINK_REPORT_JOIN_TO_INTRODUCTION_GROUPS,
                headers={'Content-Type': 'application/json'},
                json={
                    'student_id': student_id,
                    'tel_number': tel_number,
                    'discipline': discipline,
                    'zoom_url': zoom_url,
                    'teacher_id': teacher_id,
                    'teacher_name': teacher_name,
                    'datetime_start_moscow': datetime_start_moscow,
                    'datetime_start_client_tz': datetime_start_client_tz,
                    'datetime_first_summer_lesson_moscow': datetime_first_summer_lesson_moscow,
                    'datetime_first_summer_lesson_client_tz': datetime_first_summer_lesson_client_tz,
                    'datetime_second_summer_lesson_moscow': datetime_second_summer_lesson_moscow,
                    'datetime_second_summer_lesson_client_tz': datetime_second_summer_lesson_client_tz,
                    'join_type': join_type,
                    'date_end': date_end,
                },
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status', False):
                    log.warning(f'Success: {response.status} {response.text}. Отчет отправлен в amo.')
                    return True
                else:
                    log.error(f'Error: {response.status} {response.text}. Ошибка отправки отчета в amo. #333')
            else:
                log.error(f'Error: {response.status}. Ошибка отправки отчета по записи на ВМ в amo. #222')
                return False


async def send_nothing_fit_units_to_amo(student_id, msg, func: int = 0) -> bool:
    """
    Отправляет в AMO информацию от клиента, что группы на вводный модуль ему не подошли.
    Отправляется student_id, msg, tel_number на указанный адрес.
    @param func: 0 - не подошло родителю, 1 неверный код-слот или не найдена группа
    @param student_id: Сквозное поле между HH и AMO.
    @param msg: Сообщение от клиента.
    @return:
    """
    HHManager = CustomHHApiV2Manager()
    student = await HHManager.get_student_by_amo_id(student_amo_id=student_id)
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=settings.AMOLINK_NOTHING_FIT_INTRODUCTION_GROUPS,
                headers={'Content-Type': 'application/json'},
                json={
                    'func': func,
                    # 'func': 1,
                    'student_id': student_id,
                    'msg': msg,
                    'tel_number': student['Agents'][0]['Mobile']
                },
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status', False):
                    return True
                else:
                    log.error(f'Error: {response.status} {response.text}. Ошибка отправки сообщения клиента в amo.')
            else:
                log.error(f'Error: {response.status}. Ошибка отправки сообщения клиента в amo.')
                return False
