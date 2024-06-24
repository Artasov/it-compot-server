import asyncio
import logging
from datetime import datetime, timedelta
from pprint import pprint

import aiohttp

from apps.tools.exceptions.common import PaymentException, StudentByAmoIdNotFound
from service.common.common import calculate_age
from service.hollihop.classes.hollihop import HolliHopApiV2Manager
from service.hollihop.consts import amo_hh_currencies, amo_hh_pay_methods

log = logging.getLogger('base')


class SetCommentError(BaseException):
    pass


class CustomHHApiV2Manager(HolliHopApiV2Manager):

    async def set_comment_for_student_ed_unit(
            self, ed_unit_id: int, student_client_id: int, date: str, passed: bool, description: str
    ) -> None:
        """
        date: Строка формата YYYY-MM-DD
        """
        first_pass = not passed
        second_pass = passed

        await self.setStudentPasses(like_array=[{
            'Date': date,
            'EdUnitId': ed_unit_id,
            'StudentClientId': student_client_id,
            'Pass': first_pass
        }])

        result = await self.setStudentPasses(like_array=[{
            'Date': date,
            'EdUnitId': ed_unit_id,
            'StudentClientId': student_client_id,
            'Description': description,
            'Pass': second_pass
        }])

        if not result.get('success'):
            raise SetCommentError('Ошибка при добавлении комментария')

    @staticmethod
    def get_student_or_student_unit_extra_field_value(obj: dict, extra_field_name: str):
        extra_fields = obj.get('StudentExtraFields', []) + obj.get('ExtraFields', [])
        for field in extra_fields:
            if field['Name'] == extra_field_name:
                return field['Value']

    async def add_user_extra_field(self, student: dict, field_name: str, field_value: str):
        current_fields = student.get('ExtraFields', [])
        # Преобразуем текущие поля в формат, требуемый для API
        fields_for_api = [{'name': field['Name'], 'value': field['Value']} for field in current_fields]

        # Проверяем, существует ли уже поле с таким именем
        field_index = next((i for i, field in enumerate(fields_for_api) if field['name'] == field_name), None)

        if field_index is not None:
            # Если поле уже существует, обновляем его значение
            fields_for_api[field_index]['value'] = field_value
        else:
            # Если поля нет, добавляем его в формате, требуемом API
            fields_for_api.append({'name': field_name, 'value': field_value})

        # Отправляем обновленные поля
        response = await self.editUserExtraFields(
            studentClientId=student['ClientId'],
            fields=fields_for_api
        )

        return response

    async def get_ed_unit_students_by_unit_id(self, ids: list[int] | tuple[int]):
        tasks = [self.getEdUnitStudents(edUnitId=id, maxTake=100) for id in ids]
        results = await asyncio.gather(*tasks)
        return [item for sublist in results if sublist for item in sublist]

    async def get_student_by_amo_id(self, student_amo_id: int):
        students = await self.getStudents(
            extraFieldName='id ученика',
            extraFieldValue=student_amo_id,
            maxTake=1
        )
        if not students:
            raise StudentByAmoIdNotFound(student_amo_id)
        return students[0]

    async def get_active_teachers(self):
        teachers = await self.getTeachers(take=10000)
        active_teachers = []
        if teachers is not None:
            for teacher in teachers:
                # Проверяем, что у преподавателя есть статус и он не равен "уволен"
                if teacher.get('Status', '').lower() != 'уволен':
                    active_teachers.append(teacher)
        return active_teachers

    async def get_active_teachers_short_names(self) -> list:
        all_teachers = await self.get_active_teachers()
        short_names_teachers = []
        for teacher in all_teachers:
            try:
                last_name = teacher['LastName']
            except KeyError:
                last_name = ''
            try:
                first_name_short = teacher['FirstName'][0]
            except KeyError:
                first_name_short = ''
            try:
                middle_name_short = teacher['MiddleName'][0]
            except KeyError:
                middle_name_short = ''
            fio = ''
            if last_name:
                fio += last_name
            if first_name_short:
                fio += f' {first_name_short}.'
            if middle_name_short:
                fio += f' {middle_name_short}.'
            if fio:
                short_names_teachers.append(fio)
        return short_names_teachers

    @staticmethod
    async def is_ed_unit_start_in_date_range(unit, start_date: datetime, end_date: datetime):
        begin_date_str = unit['ScheduleItems'][0]['BeginDate']  # Например, '2024-01-31'
        begin_time_str = unit['ScheduleItems'][0]['BeginTime']  # Например, '10:00'
        begin_datetime_str = f"{begin_date_str} {begin_time_str}"
        begin_datetime = datetime.strptime(begin_datetime_str, '%Y-%m-%d %H:%M')
        return True if start_date <= begin_datetime <= end_date else False

    @staticmethod
    def is_ed_unit_has_lessons_in_date_range(unit, start_date: datetime, end_date: datetime):
        for day in unit['Days']:
            lesson_date = datetime.strptime(day['Date'], '%Y-%m-%d')
            # print(f'{start_date.date()} <= {lesson_date.date()} <= {end_date.date()}')
            if start_date.date() <= lesson_date.date() <= end_date.date():
                return True
        return False

    @staticmethod
    async def get_parent_email(student):
        parent_identifiers = ['мама', 'папа', 'родитель']
        for agent in student.get('Agents', []):
            if agent.get('WhoIs', '').lower() in parent_identifiers:
                return agent.get('EMail')
        return None

    @staticmethod
    async def is_ed_unit_student_end_date_in_future(unitStudent):
        end_date_str = unitStudent['EndDate']
        end_time_str = unitStudent['EndTime']
        end_datetime_str = f"{end_date_str} {end_time_str}"
        end_date = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M')
        return True if end_date > datetime.now() else False

    async def is_ed_unit_start_in_date_range_for_all_teachers(
            self, group, start_date: datetime, end_date: datetime
    ) -> bool:
        HHManager = HolliHopApiV2Manager()
        try:  # Если есть список учителей
            teacher_ids = [teacher['TeacherId'] for teacher in group['TeacherPrices']]
            for teacher_id in teacher_ids:
                fGroupT = await HHManager.getEdUnits(id=group['Id'], teacherId=teacher_id)
                try:  # Если почему-то выдает 2 педагога, но в группе 1. Когда-то давно был и сменили
                    if not await self.is_ed_unit_start_in_date_range(fGroupT[0], start_date, end_date):
                        return False
                except IndexError:
                    pass
        except KeyError:
            if not await self.is_ed_unit_start_in_date_range(group, start_date, end_date):
                return False
        return True

    async def get_teacher_by_email(self, email):
        teachers = await self.get_active_teachers()
        for teacher in teachers:
            if teacher['EMail'].lower() == email.lower():
                return teacher

    async def get_full_teacher_name_by_email(self, email):
        teacher = await self.get_teacher_by_email(email)
        return f'{teacher["LastName"]} {teacher["FirstName"]} {teacher["MiddleName"]}'

    @staticmethod
    def filter_ed_units_with_days_later_than_date(units: list, date: datetime) -> list[dict]:
        """Фильтрует массив учебных единиц у которых все дни(занятия) позже даты(date) включительно"""
        return [
            unit for unit in units
            if 'Days' in unit and all(datetime.strptime(day['Date'], '%Y-%m-%d') >= date for day in unit['Days'])
        ]

    @staticmethod
    def filter_ed_units_with_days_earlier_than_date(units: list, date: datetime) -> list[dict]:
        """Фильтрует массив учебных единиц у которых все дни(занятия) раньше даты(date) включительно"""
        return [
            unit for unit in units
            if 'Days' in unit and all(datetime.strptime(day['Date'], '%Y-%m-%d') <= date for day in unit['Days'])
        ]

    @staticmethod
    def filter_ed_units_with_any_days_later_than_date(units: list, date: datetime) -> list[dict]:
        """Фильтрует массив учебных единиц у которых есть хотя бы один день(занятие) позже даты(date) включительно"""
        return [
            unit for unit in units
            if 'Days' in unit and any(
                not day.get('Pass', False) and datetime.strptime(day['Date'], '%Y-%m-%d') >= date for day in
                unit['Days'])
        ]

    @staticmethod
    def filter_ed_units_with_any_days_earlier_than_date(units: list, date: datetime) -> list[dict]:
        """Фильтрует массив учебных единиц у которых есть хотя бы один день(занятие) раньше даты(date) включительно"""
        return [
            unit for unit in units
            if 'Days' in unit and any(
                not day.get('Pass', False) and datetime.strptime(day['Date'], '%Y-%m-%d') <= date for day in
                unit['Days'])
        ]

    async def get_ed_units_with_day_in_daterange(
            self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[dict]:
        """Возвращает учебные единицы имеющие хотя бы один день в указанном диапазоне"""
        ed_units = await self.getEdUnits(
            maxTake=10000,
            batchSize=1000,
            queryDays=True,
            **kwargs
        )
        # print(ed_units)
        return [unit for unit in ed_units if
                self.is_ed_unit_has_lessons_in_date_range(
                    unit=unit,
                    start_date=start_date,
                    end_date=end_date)]

    async def get_ed_units_with_filtered_days_in_daterange(
            self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[dict]:
        return [
            self.filter_ed_unit_days_by_daterange(unit, start_date, end_date)
            for unit in await self.get_ed_units_with_day_in_daterange(
                start_date=start_date, end_date=end_date, **kwargs
            )
        ]

    @staticmethod
    def filter_ed_unit_days_by_daterange(
            ed_unit: dict, start_date: datetime, end_date: datetime
    ) -> dict:
        filtered_days = []
        for day in ed_unit['Days']:
            date = datetime.strptime(day['Date'], '%Y-%m-%d')
            if start_date.date() <= date.date() <= end_date.date():
                filtered_days.append(day)
        ed_unit['Days'] = filtered_days
        return ed_unit

    async def get_student_by_client_id(self, session, client_id):
        student_data = await self.getStudents(clientId=client_id, maxTake=1, session=session)
        return student_data

    async def get_students_by_client_ids(self, ids: tuple | list):
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_student_by_client_id(session, client_id) for client_id in ids]
            students = await asyncio.gather(*tasks)
        return [student[0] for student in students if student]

    async def get_available_future_starting_ed_units(self, **kwargs) -> list:
        level = kwargs.pop('level', None)
        age = kwargs.pop('age', None)
        discipline = kwargs.get('discipline', None)

        search_levels = []
        if level is not None:
            if level == 'Easy':
                search_levels.append('Easy')
                search_levels.append('Easy-medium')
            elif level == 'Easy-medium':
                search_levels.append('Easy')
                search_levels.append('Easy-medium')
                search_levels.append('Medium')
            elif level == 'Medium':
                search_levels.append('Easy-medium')
                search_levels.append('Medium')
                search_levels.append('Medium-hard')
            elif level == 'Medium-hard':
                search_levels.append('Medium')
                search_levels.append('Medium-hard')
                search_levels.append('Hard')
            elif level == 'Hard':
                search_levels.append('Hard')
                search_levels.append('Medium')
                search_levels.append('Medium-hard')
        now = datetime.now()

        # DIS = await self.getDisciplines()
        # pprint(DIS)

        edUnits = await self.getEdUnits(
            # id=18111,
            disciplines=discipline,
            dateFrom=(now - timedelta(days=60)).strftime("%Y-%m-%d"),
            dateTo=(now + timedelta(days=60)).strftime("%Y-%m-%d"),
            maxTake=10000,
            batchSize=1000,
            **kwargs
        )
        # Фильтруем по вместимости
        edUnitsAvailableForJoin = [
            unit for unit in edUnits if
            int(unit.get('Vacancies')) > 0
        ]
        edUnitsAvailableForJoinFromToday = self.filter_ed_units_with_days_later_than_date(
            edUnitsAvailableForJoin, now)

        # print(f'edUnitsAvailableForJoinFromToday count: {len(edUnitsAvailableForJoinFromToday)}')
        # print([int(unit['Id']) for unit in edUnitsAvailableForJoinFromToday])
        # pprint(edUnitsAvailableForJoinFromToday)
        # Фильтруем по времени позже чем сейчас
        # для каждого преподавателя побывавшего в группе
        edUnitsFromNowAvailableForJoin = [
            unit for unit in edUnitsAvailableForJoinFromToday
            if await self.is_ed_unit_start_in_date_range_for_all_teachers(
                unit,
                now,
                now + timedelta(weeks=3))
        ]
        # log.info(f'EdUnits count: {len(edUnitsFromNowAvailableForJoin)}')
        # log.info([int(unit['Id']) for unit in edUnitsFromNowAvailableForJoin])
        # print(f'EdUnits count: {len(edUnitsFromNowAvailableForJoin)}')
        # print([int(unit['Id']) for unit in edUnitsFromNowAvailableForJoin])

        edUnitsStudent = await self.get_ed_unit_students_by_unit_id(
            [int(unit['Id']) for unit in edUnitsFromNowAvailableForJoin]
        )
        # log.info(f'Count edUnitsStudent: {len(edUnitsStudent)}')
        # log.info([(int(unitS['EdUnitId']), int(unitS['StudentClientId']))
        #           for unitS in edUnitsStudent])
        # Проверяем подходит ли нам какая-либо группа
        # Сначала получаем уникальные ID всех студентов из всех групп
        unique_student_ids = set()
        for unitS in edUnitsStudent:
            unique_student_ids.add(int(unitS['StudentClientId']))
        # Преобразуем set в tuple для запроса
        student_ids_tuple = tuple(set(unique_student_ids))
        # Получаем информацию по всем студентам одним запросом
        all_students_info = await self.get_students_by_client_ids(student_ids_tuple)

        # print(f'{all_students_info[:2]=}')
        # print(f'{student_ids_tuple=}')
        # Преобразуем результат в словарь для удобства доступа
        students_info_dict = {student['ClientId']: student for student in all_students_info}
        # print(f'{students_info_dict.keys()=}')
        # Проверяем каждую группу
        resultUnits = []
        # pprint('edUnitsFromNowAvailableForJoin')
        # pprint(len(edUnitsFromNowAvailableForJoin))
        # pprint(edUnitsFromNowAvailableForJoin)
        for unit in edUnitsFromNowAvailableForJoin:
            allow = True
            students_ids = [int(unitS['StudentClientId']) for unitS in edUnitsStudent if
                            unitS['EdUnitId'] == unit['Id']]
            # print(f'{students_ids=}')
            students_ids_set = set(students_ids)  # Уникализируем ID студентов в группе
            # Если в группе еще пусто
            if not students_ids_set:
                resultUnits.append(unit)
                # print(f'EdUnit {unit["Id"]}: Подходит Пустая')
                continue
            # Используем предварительно полученную информацию о студентах
            students = [students_info_dict[student_id] for student_id in students_ids_set if
                        student_id in students_info_dict]
            # print('StudentSSSSSSSS')
            # pprint(students)
            for student in students:
                # Если возраст отличается больше чем на 2 от запрошенного, то скип
                # print(f'AGE: {age}')
                if age is not None:
                    try:
                        student_age = calculate_age(student['Birthday'])
                        # print(student_age)
                        if abs(student_age - age) > 2:
                            allow = False
                            # print(f'EdUnit {unit["Id"]}: Не подходит по возрасту')
                            break
                    except KeyError:
                        # print('Нет дня рождения')
                        continue
                # Проверяем подходит ли по уровню
                if search_levels:
                    try:  # Берем поле дисциплины:
                        disciplines = student['Disciplines']
                        for d in disciplines:
                            if d['Discipline'] == discipline:
                                if d['Level'] not in search_levels:
                                    log.info(f'EdUnit {unit["Id"]}: Не подходит по уровню')
                                    allow = False
                    except KeyError:
                        # print('Нет Disciplines Discipline Level')
                        continue
            if allow:
                resultUnits.append(unit)
                # print(f'EdUnit {unit["Id"]}: Подходит')

        # pprint('resultUnits')
        # pprint(len(resultUnits))
        return resultUnits

    async def add_hh_payment_by_amo(self, student_amo_id: int, amo_currency: str,
                                    summ: int, amo_payment_type: str, course: str):
        student = await self.get_student_by_amo_id(student_amo_id=student_amo_id)
        clientId = student['ClientId']

        # Преобразование валюты и метода оплаты из AMO в HH
        currency_symbol = amo_hh_currencies.get(amo_currency)  # По умолчанию 'руб.'
        payment_method_id = amo_hh_pay_methods.get(amo_payment_type, 1)  # По умолчанию 1

        # Формирование значения платежа
        if amo_currency == 'Рубль':
            value = f"{summ} {currency_symbol}"
        else:
            value = f"{currency_symbol}{summ}"

        payment_data = {
            "clientId": clientId,
            "officeOrCompanyId": 1,
            "value": value,
            "description": f"Добавлен автоматически за курс {course}",
            "paymentMethodId": payment_method_id,
        }
        log.critical(payment_data)
        response = await self.addPayment(**payment_data)
        if response.get('success'):
            return response
        else:
            raise PaymentException('Не добавился платеж клиента.')

    async def get_student_by_fio_or_email_or_tel(self, fio: str, email: str, tel: str) -> dict | None:
        if fio:
            students_by_fio = await self.getStudents(term=fio, maxTake=1000)
            if students_by_fio and len(students_by_fio) == 1:
                return students_by_fio[0]
        if email:
            students_by_email = await self.getStudents(term=email, maxTake=1000)
            if students_by_email and len(students_by_email) == 1:
                return students_by_email[0]
        if tel:
            students_by_tel = await self.getStudents(term=tel, maxTake=1000)
            if students_by_tel and len(students_by_tel) == 1:
                return students_by_tel[0]

    async def get_latest_ed_unit_s_for_student_on_discipline(self, client_id, discipline) -> dict | None:
        ed_units_s = await self.getEdUnitStudents(
            studentClientId=client_id, edUnitDisciplines=discipline, maxTake=1000, queryDays=True,
            dateFrom='2015-05-01', dateTo=datetime.now().strftime('%Y-%m-%d')
        )
        if not ed_units_s:
            return None
        if len(ed_units_s) == 1:
            return ed_units_s[0]
        latest_unit = None
        latest_date = None
        for unit in ed_units_s:
            for day in unit['Days']:
                if not day.get('Pass', False):
                    day_date = datetime.strptime(day['Date'], '%Y-%m-%d')
                    if latest_date is None or day_date > latest_date:
                        latest_date = day_date
                        latest_unit = unit
        return latest_unit

    @staticmethod
    def filter_latest_ed_unit_s_for_student_on_disciplines(ed_units_s):
        filtered_units = {}
        for unit in ed_units_s:
            if not unit.get('Days'): continue
            client_id = unit['StudentClientId']
            discipline = unit['EdUnitDiscipline']
            unit_key = (client_id, discipline)

            for day in unit['Days']:
                if not day.get('Pass', False):
                    day_date = datetime.strptime(day['Date'], '%Y-%m-%d')

                    if unit_key not in filtered_units:
                        filtered_units[unit_key] = (unit, day_date)
                    else:
                        _, latest_date = filtered_units[unit_key]
                        if day_date > latest_date:
                            filtered_units[unit_key] = (unit, day_date)

        return [unit for unit, _ in filtered_units.values()]

    @staticmethod
    def get_last_day_desc(ed_unit_s):
        last_day = None

        # Проходим по всем дням
        for day in ed_unit_s.get('Days', []):
            if day.get('Pass'):
                continue
            date = day.get('Date')
            if isinstance(date, datetime):
                date = date.strftime('%Y-%m-%d')
            day_date = datetime.strptime(date, '%Y-%m-%d')
            if last_day is None or day_date > last_day['Date']:
                last_day = day
                last_day['Date'] = day_date

        if last_day:
            return last_day.get('Description')
        return None

    @staticmethod
    def filter_ed_units_by_extra_field(ed_units: list | tuple, extra_field_name: str, extra_field_value) -> list:
        filtered_units = []

        for unit in ed_units:
            for extra_field in unit.get('ExtraFields', []):
                if extra_field.get('Name') == extra_field_name and extra_field.get('Value') == extra_field_value:
                    filtered_units.append(unit)
                    break

        return filtered_units

    async def is_student_in_group_on_discipline(self, student_amo_id, discipline) -> bool:
        """
        Проверяет через HolliHop api учится ли уже ученик по данной дисциплине.
        Есть ли такие EdUnitStudent discipline=discipline со стартом в будущем.
        @param student_amo_id: Сквозной id ученика amo hh
        @param discipline: Одно из направлений из списка в amo_levels consts.py
        @return: bool
        """
        student = await self.get_student_by_amo_id(student_amo_id=student_amo_id)
        result = await self.getEdUnitStudents(
            edUnitTypes='Group,MiniGroup',
            studentClientId=student['ClientId'],
            edUnitDisciplines=discipline,
            dataFrom=datetime.now().strftime('%Y-%m-%d'),
            maxTake=1000
        )
        result = [unit for unit in result if await self.is_ed_unit_student_end_date_in_future(unit)]
        return bool(result)
