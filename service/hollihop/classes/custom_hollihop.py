import asyncio
import logging
from datetime import datetime, timedelta

from service.common.common import calculate_age
from service.hollihop.classes.hollihop import HolliHopApiV2Manager

log = logging.getLogger('base')


class CustomHHApiV2Manager(HolliHopApiV2Manager):
    async def getEdUnitStudentsByUnitId(self, ids: list[int, ...] | tuple[int, ...]):
        tasks = [self.get_ed_unit_student(edUnitId=id) for id in ids]
        results = await asyncio.gather(*tasks)
        return [item for sublist in results if sublist for item in sublist]

    def getActiveTeachers(self):
        teachers = self.get_teachers(take=10000)
        active_teachers = []

        if teachers is not None:
            for teacher in teachers:
                # Проверяем, что у преподавателя есть статус и он не равен "уволен"
                if teacher.get('Status', '').lower() != 'уволен':
                    active_teachers.append(teacher)

        return active_teachers

    def getActiveTeachersShortNames(self) -> list:
        all_teachers = self.getActiveTeachers()
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
    async def isEdUnitStartInDateRange(group, start_date: datetime, end_date: datetime):
        begin_date_str = group['ScheduleItems'][0]['BeginDate']  # Например, '2024-01-31'
        begin_time_str = group['ScheduleItems'][0]['BeginTime']  # Например, '10:00'
        begin_datetime_str = f"{begin_date_str} {begin_time_str}"
        begin_datetime = datetime.strptime(begin_datetime_str, '%Y-%m-%d %H:%M')

        return True if start_date <= begin_datetime <= end_date else False

    async def isEdUnitStartInDateRangeForAllTeachers(
            self, group, start_date: datetime, end_date: datetime
    ) -> bool:
        HHManager = HolliHopApiV2Manager()

        try:  # Если есть список учителей
            teacher_ids = [teacher['TeacherId'] for teacher in group['TeacherPrices']]
            for teacher_id in teacher_ids:
                fGroupT = await HHManager.get_ed_units(id=group['Id'], teacherId=teacher_id)
                try:  # Если почему-то выдает 2 педагога, но в группе 1. Когда-то давно был и сменили
                    if not await self.isEdUnitStartInDateRange(fGroupT[0], start_date, end_date):
                        return False
                except IndexError:
                    pass
        except KeyError:
            if not await self.isEdUnitStartInDateRange(group, start_date, end_date):
                return False
        return True

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

        # Фильтруем по вместимости
        edUnitsFromTodayAvailableForJoin = [
            unit for unit in edUnitsFromToday if
            unit.get('StudentsCount') < unit.get('StudentsCount') + unit.get(
                'Vacancies')
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

        edUnitsStudent = await self.getEdUnitStudentsByUnitId(
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
        all_students_info = await self.get_students(
            extraFieldName='id ученика',
            extraFieldValue=','.join(map(str, student_ids_tuple))
        )
        # Преобразуем результат в словарь для удобства доступа
        students_info_dict = {student['id']: student for student in all_students_info}

        # Проверяем каждую группу
        resultUnits = []
        for unit in edUnitsFromNowAvailableForJoin:
            allow = True
            students_ids = [int(unitS['StudentClientId']) for unitS in edUnitsStudent if
                            unitS['EdUnitId'] == unit['Id']]
            students_ids_set = set(students_ids)  # Уникализируем ID студентов в группе

            # Если в группе еще пусто
            if not students_ids_set:
                resultUnits.append(unit)
                log.info(f'EdUnit {unit["Id"]}: Подходит Пустая')
                continue

            # Используем предварительно полученную информацию о студентах
            students = [students_info_dict[student_id] for student_id in students_ids_set if
                        student_id in students_info_dict]

            for student in students:
                # Если возраст отличается больше чем на 2 от запрошенного, то скип
                if age is not None:
                    try:
                        student_age = calculate_age(student['Birthday'])
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
