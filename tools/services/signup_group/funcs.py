import logging
from datetime import datetime, timedelta

from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from tools.services.loggers.gsheet_logger import GSheetsSignUpFormingGroupLogger as GLog

log = logging.getLogger('base')


def sort_groups_by_datetime(groups):
    for group in groups:
        group['sort_key'] = datetime.strptime(
            group['ScheduleItems'][0]['BeginDate'] + ' ' + group['ScheduleItems'][0]['BeginTime'], "%Y-%m-%d %H:%M")
    sorted_groups = sorted(groups, key=lambda x: x['sort_key'])

    for group in sorted_groups:
        del group['sort_key']
    return sorted_groups


async def get_forming_groups_for_join(level: str, discipline: str, age: int) -> list:
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
    HHManager = CustomHHApiV2Manager()

    student = await HHManager.get_students(
        extraFieldName='id ученика',
        extraFieldValue=student_id
    )

    group_for_start = await HHManager.get_ed_units(id=group_id)

    now = datetime.now()

    if group_for_start:
        group_for_start = [
            edUnit for edUnit in group_for_start
            if await HHManager.isEdUnitStartInDateRangeForAllTeachers(
                edUnit, now, now + timedelta(weeks=3)
            )
        ]
    start_date = datetime.strptime(
        group_for_start[0]['ScheduleItems'][0]['BeginDate'], '%Y-%m-%d'
    ) + timedelta(weeks=2)

    group_course = await HHManager.get_ed_units(
        types='Group,MiniGroup',
        dateFrom=start_date.strftime('%Y-%m-%d'),  # '2023-09-11' на две недели вперед надо эту дату
        timeFrom=group_for_start[0]['ScheduleItems'][0]['BeginTime'],
        timeTo=group_for_start[0]['ScheduleItems'][0]['EndTime'],
        disciplines=group_for_start[0]['Discipline'],
        # teacherId=group_for_start[0]['ScheduleItems']['Teacher'],
    )
    group_course = [
        unit for unit in group_course
        if await HHManager.isEdUnitStartInDateRangeForAllTeachers(
            unit, start_date, start_date + timedelta(days=1)
        )
    ]
    # Логирование в гугл таблицу
    glog = GLog()
    if len(group_course) == 0:
        glog.error(
            [f'{student_id} в {group_id}'] +
            [datetime.now().strftime('%Y-%m-%d %H:%M')] +
            ['Не найдено групп через 2 недели.']
        )
        log.error('Не найдено групп через 2 недели.')
        log.error(group_course)
        raise AssertionError('Не найдено групп через 2 недели.')
    elif len(group_course) > 1:
        glog.error(
            [f'{student_id} в {group_id}'] +
            [datetime.now().strftime('%Y-%m-%d %H:%M')] +
            ['Найдено более 1ой группы через 2 недели.']
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
        glog.success(
            [f'{student_id} в {group_id} и {group_course[0]["Id"]}'] +
            [datetime.now().strftime('%Y-%m-%d %H:%M')]
        )
        return True
    else:
        glog.error(
            [f'{student_id} в {group_id} и {group_course[0]["Id"]}'] +
            [datetime.now().strftime('%Y-%m-%d %H:%M')] +
            [f'Не смог записать в группы '
             f'{group_id}={result1.get("success")} '
             f'{group_course[0]["Id"]}={result2.get("success")}']
        )
        return False


async def is_student_in_group_on_discipline(student_id, discipline) -> bool:
    HHManager = CustomHHApiV2Manager()
    student = await HHManager.get_students(
        extraFieldName='id ученика',
        extraFieldValue=student_id
    )
    result = await HHManager.get_ed_unit_students(
        edUnitTypes='Group,MiniGroup',
        studentClientId=student['ClientId'],
        edUnitDisciplines=discipline,
        dataFrom=datetime.now().strftime("%Y-%m-%d")
    )
    return bool(result)
