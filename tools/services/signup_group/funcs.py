import logging
from datetime import datetime, timedelta

import aiohttp
from django.conf import settings

from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from tools.services.loggers.gsheet_logger import GSheetsSignUpFormingGroupLogger as GLog

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


async def get_forming_groups_for_join(level: str, discipline: str, age: int) -> list:
    """
    @param level: Уровень ученика из списка amo_disciplines в consts.py
    @param discipline: Одно из направлений из списка в amo_levels consts.py
    @param age: Количество полных лет будущего ученика
    @return: Список с найденными группами по параметрам по api HolliHop
    """
    HHManager = CustomHHApiV2Manager()
    groups_available = await HHManager.getAvailableFutureStartingEdUnits(
        types='Group,MiniGroup',
        learningTypes='Вводный модуль курса (russian language)',
        statuses='Forming',
        level=level,
        discipline=discipline,
        age=age
    )
    groups_available = sort_groups_by_datetime(groups_available)

    groups_result = []
    for group in groups_available:
        groups_result.append({
            'Id': group['Id'],
            'Type': group['Type'],
            'Discipline': group['Discipline'],
            'StudentsCount': group['StudentsCount'],
            'Vacancies': group['Vacancies'],
            'ScheduleItems': group['ScheduleItems'],
            'OfficeTimeZone': group['OfficeTimeZone'],
        })
    return groups_result


async def add_student_to_forming_group(student_id, group_id) -> bool:
    """
    !!! ДЕКОМПОЗИРОВАТЬ !!!
    Добавляет студента в группу через amo api и логирует в googlesheets результат выполнения.
    @param student_id: Сквозной id ученика amo hh
    @param group_id: EdUnit['Id'] идентификатор группы
    @return: Если хоть что-то пойдет не так вернется False либо raise Error, иначе True.
    """
    HHManager = CustomHHApiV2Manager()
    glog = GLog()  # Логирование в гугл таблицу
    student = await HHManager.get_students(
        extraFieldName='id ученика',
        extraFieldValue=student_id
    )
    student = student[0]

    now = datetime.now()

    forming_group = await HHManager.get_ed_units(id=group_id)
    if forming_group:
        forming_group = [
            edUnit for edUnit in forming_group
            if await HHManager.isEdUnitStartInDateRangeForAllTeachers(
                edUnit, now, now + timedelta(weeks=3)
            )
        ]
    if not forming_group:
        glog.error(
            student_amo_id=student_id,
            student_hh_id=student['ClientId'],
            comment='Не найдена выбранная группа.'
        )
        return False
    forming_group = forming_group[0]

    start_forming_group_date = datetime.strptime(
        forming_group['ScheduleItems'][0]['BeginDate'], '%Y-%m-%d'
    )
    start_course_group_date = start_forming_group_date + timedelta(weeks=2)

    group_course = await HHManager.get_ed_units(
        types='Group,MiniGroup',
        dateFrom=start_course_group_date.strftime('%Y-%m-%d'),  # '2023-09-11' на две недели вперед надо эту дату
        timeFrom=forming_group['ScheduleItems'][0]['BeginTime'],
        timeTo=forming_group['ScheduleItems'][0]['EndTime'],
        disciplines=forming_group['Discipline'],
        # teacherId=group_for_start[0]['ScheduleItems']['Teacher'],
    )
    group_course = [
        unit for unit in group_course
        if await HHManager.isEdUnitStartInDateRangeForAllTeachers(
            unit, start_course_group_date, start_course_group_date + timedelta(days=1)
        )
    ]
    if len(group_course) == 0:
        glog.error(
            student_amo_id=student_id,
            student_hh_id=student['ClientId'],
            comment='Не найдено групп через 2 недели.'
        )
        log.error('Не найдено групп через 2 недели.')
        log.error(group_course)
        raise AssertionError('Не найдено групп через 2 недели.')
    elif len(group_course) > 1:
        glog.error(
            student_amo_id=student_id,
            student_hh_id=student['ClientId'],
            comment='Найдено более 1ой группы через 2 недели.'
        )
        log.error('Найдено более 1ой группы через 2 недели.')
        log.error(group_course)
        raise AssertionError('Найдено более 1ой группы через 2 недели.')

    result1 = await HHManager.add_ed_unit_student(
        edUnitId=group_id,
        studentClientId=student['ClientId'],
        comment=f'Добавлен(а) с помощью сайта в edUnits({group_id}, {group_course[0]["Id"]}).'
    )
    log.info(f'Student {"not " if result1.get("success", False) else ""}added in edUnit({group_id})')
    log.info(result1)

    result2 = await HHManager.add_ed_unit_student(
        edUnitId=group_course[0]['Id'],
        studentClientId=student['ClientId'],
        comment=f'Добавлен(а) с помощью сайта в edUnits({group_id}, {group_course[0]["Id"]}).'
    )
    log.info(f'Student {"not " if result2.get("success", False) else ""}added in edUnit({group_course[0]["Id"]})')
    log.info(result2)

    if result1.get('success', False) and result2.get('success', False):
        # Отправляем отчет в амо тригер чтобы проставились данные в сделку.
        report_result = send_report_join_to_forming_group(
            student_id=student_id,
            tel_number=student['Agents'][0]['Mobile'],
            zoom_url=forming_group['ScheduleItems'][0]['ClassroomLink'],
            teacher_id=forming_group['ScheduleItems'][0]['TeacherId'],
            teacher_name=forming_group['ScheduleItems'][0]['Teacher'],
            date_start=int(start_forming_group_date.timestamp()),  # Дата старта ВМ
            date_end=int(start_course_group_date.timestamp()),  # Дата старта основной группы
        )
        if report_result:
            glog.success(
                student_amo_id=student_id,
                student_hh_id=student['ClientId'],
                groups_ids=(f'{result1.get("success", False)}: {group_id}',
                            f'{result1.get("success", False)}: {group_course[0]["Id"]}'),
            )
            return True
        else:
            glog.error(
                student_amo_id=student_id,
                student_hh_id=student['ClientId'],
                groups_ids=(f'{result1.get("success", False)}: {group_id}',
                            f'{result1.get("success", False)}: {group_course[0]["Id"]}'),
                comment='Не смог отправить отчет в AMO'
            )
            return False
    else:
        glog.error(
            student_amo_id=student_id,
            student_hh_id=student['ClientId'],
            groups_ids=(f'{result1.get("success", False)}: {group_id}',
                        f'{result1.get("success", False)}: {group_course[0]["Id"]}'),
            comment='Не смог записать в группы'
        )
        return False


async def send_report_join_to_forming_group(
        student_id: int,
        tel_number: str,
        zoom_url: str,
        teacher_id: int,
        teacher_name: str,
        date_start: int,
        date_end: int,
) -> bool:
    """
    Отправляет amo триггер информацию Post запросом о добавлении ученика.
    @param student_id: Сквозной id ученика amo hh
    @param tel_number: Телефон первого найденного агента у ученика
    @param zoom_url: Ссылка для подключения на занятие в зум
    @param teacher_id: id преподавателя группы
    @param teacher_name: Его имя
    @param date_start: Дата старта вводного модуля
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
                    'zoom_url': zoom_url,
                    'teacher_id': teacher_id,
                    'teacher_name': teacher_name,
                    'date_start': date_start,
                    'date_end': date_end,
                },
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status', False):
                    return True
                else:
                    log.error(f'Error: {response.status} {response.text}. Ошибка отправки сообщения клиента в amo.')
            else:
                log.error(f'Error: {response.status}. Ошибка отправки отчета по записи на ВМ в amo.')
                return False


async def send_nothing_fit_units_to_amo(student_id, msg) -> bool:
    """
    Отправляет в AMO информацию от клиента, что группы на вводный модуль ему не подошли.
    Отправляется student_id, msg, tel_number на указанный адрес.
    @param student_id: Сквозное поле между HH и AMO.
    @param msg: Сообщение от клиента.
    @return:
    """
    HHManager = CustomHHApiV2Manager()
    student = await HHManager.get_students(
        extraFieldName='id ученика',
        extraFieldValue=student_id
    )
    student = student[0]
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=settings.AMOLINK_NOTHING_FIT_INTRODUCTION_GROUPS,
                headers={'Content-Type': 'application/json'},
                json={
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


async def is_student_in_group_on_discipline(student_id, discipline) -> bool:
    """
    Проверяет через HolliHop api учится ли уже ученик по данной дисциплине.
    Есть ли такие EdUnitStudent discipline=discipline со стартом в будущем.
    @param student_id: Сквозной id ученика amo hh
    @param discipline: Одно из направлений из списка в amo_levels consts.py
    @return: bool
    """
    HHManager = CustomHHApiV2Manager()
    student = await HHManager.get_students(
        extraFieldName='id ученика',
        extraFieldValue=student_id
    )
    student = student[0]
    result = await HHManager.get_ed_unit_students(
        edUnitTypes='Group,MiniGroup',
        studentClientId=student['ClientId'],
        edUnitDisciplines=discipline,
        dataFrom=datetime.now().strftime('%Y-%m-%d')
    )
    result = [unit for unit in result if await HHManager.isEdUnitStudentEndDateInFuture(unit)]
    return bool(result)
