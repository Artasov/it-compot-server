import logging
from datetime import datetime
from pprint import pprint

import aiohttp
from django.conf import settings

from apps.tools.services.loggers.gsheet_logger import GSheetsSignUpFormingGroupLogger as GLog
from apps.tools.services.signup_group.consts import amo_hh_disciplines_map
from apps.tools.services.signup_group.exeptions.common import UnitAlreadyFullException
from service.common.common import calculate_age
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager

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
    edUnitsStudent = await HHM.getEdUnitStudentsByUnitId([unit['Id']])
    students_ids = [int(unitS['StudentClientId']) for unitS in edUnitsStudent if
                    unitS['EdUnitId'] == unit['Id']]
    students_ids_set = set(students_ids)
    unique_student_ids = set()
    for unitS in edUnitsStudent:
        unique_student_ids.add(int(unitS['StudentClientId']))
    # Преобразуем set в tuple для запроса
    student_ids_tuple = tuple(set(unique_student_ids))
    # Получаем информацию по всем студентам одним запросом
    all_students_info = await HHM.get_students_by_ids(student_ids_tuple)
    # Преобразуем результат в словарь для удобства доступа
    students_info_dict = {student['ClientId']: student for student in all_students_info}

    # Если в группе еще пусто
    if not students_ids_set:
        return True
    # Используем предварительно полученную информацию о студентах
    students = [students_info_dict[student_id] for student_id in students_ids_set if
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


async def add_student_to_forming_group(student_id, group_id):
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

    # 1 ГРУППА
    forming_unit = (await HHManager.get_ed_units(id=group_id))[0]
    if not is_unit_vacant_for_join(unit=forming_unit):
        raise UnitAlreadyFullException

    pprint(forming_unit)

    result1 = await HHManager.add_ed_unit_student(
        edUnitId=group_id,
        studentClientId=student['ClientId'],
        comment=f'Добавлен(а) с помощью сайта в edUnits({group_id}).'
    )
    start_forming_unit_date = datetime.strptime(forming_unit['ScheduleItems'][0]['BeginDate'], '%Y-%m-%d')
    start_forming_group_time = datetime.strptime(forming_unit['ScheduleItems'][0]['BeginTime'], '%H:%M')

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
        report_result = await send_report_join_to_forming_group(
            student_id=student_id,
            tel_number=student['Agents'][0]['Mobile'],
            discipline=next(
                (amo for amo, hh in amo_hh_disciplines_map if hh == forming_unit['Discipline']),
                "Дисциплина не найдена"),
            zoom_url=forming_unit['ScheduleItems'][0]['ClassroomLink'],
            teacher_id=forming_unit['ScheduleItems'][0]['TeacherId'],
            teacher_name=forming_unit['ScheduleItems'][0]['Teacher'],
            datetime_start=int(datetime.combine(
                start_forming_unit_date.date(),
                start_forming_group_time.time()).timestamp()),  # Дата и время старта ВМ
            date_end=int(start_forming_unit_date2.timestamp()) if start_forming_unit_date2 else 0,  # Дата окончания ВМ
        )
        if not report_result:
            glog.error(
                student_amo_id=student_id,
                student_hh_id=student['Id'],
                groups_ids=(f'{result1.get("success", False)}: {group_id}',
                            f'{result1.get("success", False)}: '),
                comment='Не смог отправить отчет в AMO'
            )
        glog.success(
            student_amo_id=student_id,
            student_hh_id=student['Id'],
            groups_ids=(f'{result1.get("success", False)}: {group_id}',),
            comment='Записал на вводный модуль'
        )

    # 2 ГРУППА
    if forming_unit.get('ExtraFields'):
        slot_code = next((field['Value'] for field in forming_unit['ExtraFields'] if field['Name'] == 'код-слот'), None)
        course_unit_error = ''
        if not slot_code:
            course_unit_error = 'Не найдено поля код-слот'
        if str(slot_code)[-1] != '1':
            course_unit_error = 'Код-слот вводного модуля не равен 1.'
        # Если код-слот верный
        if not course_unit_error:
            course_unit = await HHManager.get_ed_units(
                extraFieldName='код-слот',
                extraFieldValue=str(slot_code)[:-1] + '2'
            )
            if len(course_unit) == 0:
                course_unit_error = f'Не найдено группы с кодом {str(slot_code)[:-1] + "2"}.'
            elif len(course_unit) > 1:
                course_unit_error = f'Найдено более 1ой группы с кодом {slot_code}.'

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
                result2 = await HHManager.add_ed_unit_student(
                    edUnitId=course_unit[0]['Id'],
                    studentClientId=student['ClientId'],
                    comment=f'Добавлен(а) с помощью сайта в edUnits({group_id}, {course_unit[0]["Id"]}).'
                )
                if result2.get('success'):
                    glog.success(
                        student_amo_id=student_id,
                        student_hh_id=student['Id'],
                        groups_ids=(f'{result1.get("success", False)}: {group_id}',),
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
        open_personal_profile_result = await HHManager.set_student_auth_info(
            studentClientId=student['ClientId'],
            login=await HHManager.get_parent_email(student),
            password='2146648'
        )
        if not open_personal_profile_result.get('success'):
            glog.error(
                student_amo_id=student_id,
                student_hh_id=student['Id'],
                groups_ids=(f'{result1.get("success", False)}: {group_id}',
                            f'{result1.get("success", False)}: '),
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
            glog.error(
                student_amo_id=student_id,
                student_hh_id=student['Id'],
                groups_ids=(f'{result1.get("success", False)}: {group_id}',
                            f'{result1.get("success", False)}: '),
                comment='Личный кабинет открыт, amo ссылка НЕ установлена'
            )
        glog.success(
            student_amo_id=student_id,
            student_hh_id=student['Id'],
            groups_ids=(f'{result1.get("success", False)}: {group_id}',
                        f'{result1.get("success", False)}: '),
            comment='Личный кабинет открыт, amo ссылка установлена'
        )


async def send_report_join_to_forming_group(
        student_id: int,
        tel_number: str,
        discipline: str,
        zoom_url: str,
        teacher_id: int,
        teacher_name: str,
        datetime_start: int,
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
    @param datetime_start: Дата и время старта вводного модуля
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
                    'datetime_start': datetime_start,
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
