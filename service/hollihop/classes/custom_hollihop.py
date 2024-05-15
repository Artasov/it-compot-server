import asyncio
import logging
from datetime import datetime, timedelta

from apps.tools.exeptions.common import PaymentException
from service.common.common import calculate_age
from service.hollihop.classes.hollihop import HolliHopApiV2Manager
from service.hollihop.consts import amo_hh_currencies, amo_hh_pay_methods

log = logging.getLogger('base')


class SetCommentError(BaseException):
    pass


class CustomHHApiV2Manager(HolliHopApiV2Manager):

    async def set_comment_for_student_ed_unit(
            self, ed_unit_id: int, student_client_id: int, date: str, description: str
    ) -> None:
        """
        date: Строка формата YYYY-MM-DD
        """
        await self.set_student_passes(**{
            'like_array': [
                {
                    'Date': date,
                    'EdUnitId': ed_unit_id,
                    'StudentClientId': student_client_id,
                    'Pass': True
                }
            ]
        })
        result = await self.set_student_passes(**{
            'like_array': [
                {
                    'Date': date,
                    'EdUnitId': ed_unit_id,
                    'StudentClientId': student_client_id,
                    'Description': description,
                    'Pass': False
                }
            ]
        })
        if not result.get('success'):
            raise SetCommentError('Ошибка при добавлении комментария')

    async def get_ed_unit_students_by_unit_id(self, ids: list[int, ...] | tuple[int, ...]):
        tasks = [self.get_ed_unit_student(edUnitId=id) for id in ids]
        results = await asyncio.gather(*tasks)
        return [item for sublist in results if sublist for item in sublist]

    async def getActiveTeachers(self):
        teachers = await self.get_teachers(take=10000)
        active_teachers = []
        if teachers is not None:
            for teacher in teachers:
                # Проверяем, что у преподавателя есть статус и он не равен "уволен"
                if teacher.get('Status', '').lower() != 'уволен':
                    active_teachers.append(teacher)
        return active_teachers

    async def getActiveTeachersShortNames(self) -> list:
        all_teachers = await self.getActiveTeachers()
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
    async def isEdUnitStudentEndDateInFuture(unitStudent):
        end_date_str = unitStudent['EndDate']
        end_time_str = unitStudent['EndTime']
        end_datetime_str = f"{end_date_str} {end_time_str}"
        end_date = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M')
        return True if end_date > datetime.now() else False

    async def isEdUnitStartInDateRangeForAllTeachers(
            self, group, start_date: datetime, end_date: datetime
    ) -> bool:
        HHManager = HolliHopApiV2Manager()
        try:  # Если есть список учителей
            teacher_ids = [teacher['TeacherId'] for teacher in group['TeacherPrices']]
            for teacher_id in teacher_ids:
                fGroupT = await HHManager.get_ed_units(id=group['Id'], teacherId=teacher_id)
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
        teachers = await self.getActiveTeachers()
        for teacher in teachers:
            if teacher['EMail'] == email:
                return teacher

    async def get_ed_units_in_daterange(self, start_date: datetime, end_date: datetime, **kwargs) -> list[dict]:
        """Возвращает учебные единицы имеющие хотя бы один день в указанном диапазоне"""
        ed_units = await self.get_ed_units(
            maxTake=10000,
            batchSize=1000,
            **kwargs
        )
        # print(ed_units)
        return [unit for unit in ed_units if
                self.is_ed_unit_has_lessons_in_date_range(
                    unit=unit,
                    start_date=start_date,
                    end_date=end_date)]

    async def get_ed_units_with_days_in_daterange(
            self, start_date: datetime, end_date: datetime, **kwargs
    ) -> list[dict]:
        return [
            self.filter_ed_unit_days_by_daterange(unit, start_date, end_date)
            for unit in await self.get_ed_units_in_daterange(
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

    async def getAvailableFutureStartingEdUnits(self, **kwargs) -> list:
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

        # DIS = await self.get_disciplines()
        # pprint(DIS)

        edUnitsFromToday = await self.get_ed_units(
            # id=18111,
            queryTeacherPrices='true',
            disciplines=discipline,
            # queryDays='true',
            dateFrom=now.strftime("%Y-%m-%d"),
            maxTake=10000,
            batchSize=1000,
            **kwargs
        )
        # print(f'EdUnits count: {len(edUnitsFromToday)}')
        # print([int(unit['Id']) for unit in edUnitsFromToday])
        # Фильтруем по вместимости
        edUnitsFromTodayAvailableForJoin = [
            unit for unit in edUnitsFromToday if
            int(unit.get('Vacancies')) > 0
        ]
        # Фильтруем по времени позже чем сейчас
        # для каждого преподавателя побывавшего в группе
        edUnitsFromNowAvailableForJoin = [
            unit for unit in edUnitsFromTodayAvailableForJoin
            if await self.isEdUnitStartInDateRangeForAllTeachers(
                unit,
                now,
                now + timedelta(weeks=3))
        ]
        log.info(f'EdUnits count: {len(edUnitsFromNowAvailableForJoin)}')
        log.info([int(unit['Id']) for unit in edUnitsFromNowAvailableForJoin])
        # print(f'EdUnits count: {len(edUnitsFromNowAvailableForJoin)}')
        # print([int(unit['Id']) for unit in edUnitsFromNowAvailableForJoin])

        edUnitsStudent = await self.get_ed_unit_students_by_unit_id(
            [int(unit['Id']) for unit in edUnitsFromNowAvailableForJoin]
        )
        log.info(f'Count edUnitsStudent: {len(edUnitsStudent)}')
        log.info([(int(unitS['EdUnitId']), int(unitS['StudentClientId']))
                  for unitS in edUnitsStudent])
        # Проверяем подходит ли нам какая-либо группа
        # Сначала получаем уникальные ID всех студентов из всех групп
        unique_student_ids = set()
        for unitS in edUnitsStudent:
            unique_student_ids.add(int(unitS['StudentClientId']))
        # Преобразуем set в tuple для запроса
        student_ids_tuple = tuple(set(unique_student_ids))
        # Получаем информацию по всем студентам одним запросом
        all_students_info = await self.get_students_by_ids(student_ids_tuple)

        # print(f'{all_students_info[:2]=}')
        # print(f'{student_ids_tuple=}')
        # Преобразуем результат в словарь для удобства доступа
        students_info_dict = {student['ClientId']: student for student in all_students_info}
        # print(f'{students_info_dict.keys()=}')
        # Проверяем каждую группу
        resultUnits = []
        for unit in edUnitsFromNowAvailableForJoin:
            allow = True
            students_ids = [int(unitS['StudentClientId']) for unitS in edUnitsStudent if
                            unitS['EdUnitId'] == unit['Id']]
            # print(f'{students_ids=}')
            students_ids_set = set(students_ids)  # Уникализируем ID студентов в группе
            # Если в группе еще пусто
            if not students_ids_set:
                resultUnits.append(unit)
                log.info(f'EdUnit {unit["Id"]}: Подходит Пустая')
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
                            log.info(f'EdUnit {unit["Id"]}: Не подходит по возрасту')
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
                log.info(f'EdUnit {unit["Id"]}: Подходит')
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
        response = await self.add_payment(**payment_data)
        if response.get('success'):
            return response
        else:
            raise PaymentException('Не добавился платеж клиента.')
