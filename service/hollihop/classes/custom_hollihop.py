import time
from datetime import datetime
from pprint import pprint

from service.common.common import calculate_age
from service.hollihop.classes.hollihop import HolliHopApiV2Manager


class CustomHHApiV2Manager(HolliHopApiV2Manager):
    def getActiveTeachers(self):
        teachers = self.getTeachers(take=10000)
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
    async def isGroupInFuture(group):
        begin_date_str = group['ScheduleItems'][0]['BeginDate']  # например, '2024-01-31'
        begin_time_str = group['ScheduleItems'][0]['BeginTime']  # например, '10:00'

        begin_datetime_str = f"{begin_date_str} {begin_time_str}"
        begin_datetime = datetime.strptime(begin_datetime_str, '%Y-%m-%d %H:%M')

        if begin_datetime > datetime.now():
            return True
        else:
            return False

    async def isGroupInFutureForAllTeachers(self, group):
        if group['Id'] == 17978:
            pprint(group)
        HHManager = HolliHopApiV2Manager()

        try:  # Если есть список учителей
            teacher_ids = [teacher['TeacherId'] for teacher in group['TeacherPrices']]
            for teacher_id in teacher_ids:
                fGroupT = await HHManager.getEdUnits(id=group['Id'], teacherId=teacher_id)
                try:  # Если почему-то выдает 2 педагога, но в группе 1. Когда-то давно был и сменили
                    if not await self.isGroupInFuture(fGroupT[0]):
                        return False
                except IndexError:
                    pass
        except KeyError:
            if not await self.isGroupInFuture(group):
                return False

        return True

    async def get_forming_groups(self, level: str, discipline: str, age: int) -> list:
        search_levels = []
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

        now = datetime.now().strftime("%Y-%m-%d")

        # forming groups
        formingGroups = await self.getEdUnits(
            # id=18111,
            queryTeacherPrices='true',
            types='Group,MiniGroup',
            queryDays='true',
            statuses='Forming',
            learningTypes='Вводный модуль курса (russian language)',
            disciplines=discipline,
            dateFrom=now,
            maxTake=10000,
            batchSize=1000
        )

        formingGroups = [fGroup for fGroup in formingGroups
                         if await self.isGroupInFutureForAllTeachers(fGroup)]

        # pprint(formingGroups[0])
        print(f'Forming groups count: {len(formingGroups)}')
        print([int(value['Id']) for value in formingGroups])
        # return

        sGroups = await self.getEdUnitStudentsByUnitId(
            [int(value['Id']) for value in formingGroups]
        )
        print(f'Count sGroups: {len(sGroups)}')
        ids = [(int(sGroup['EdUnitId']), int(sGroup['StudentClientId']))
               for sGroup in sGroups]
        print(ids)
        result_groups = []
        # Проверяем подходит ли нам какая-либо группа
        for formingGroup in formingGroups:
            allow = True
            # Получаем id студентов этой группы
            students_ids = []
            for sGroup in sGroups:
                if sGroup['EdUnitId'] == formingGroup['Id']:
                    students_ids.append(int(sGroup['StudentClientId']))
            students_ids = tuple(set(students_ids))
            # print(f'{formingGroup["Id"]} - {students_ids}')

            # Если в группе еще пусто
            if len(students_ids) == 0:
                result_groups.append(formingGroup)
                print(f'GROUP {formingGroup["Id"]}: Подходит Пустая')
                continue

            # Получаем информацию по студентам
            students = await self.getStudentsByIds(students_ids)

            for student in students:
                # Если возраст отличается больше чем на 2 от запрошенного, то скип
                try:
                    student_age = calculate_age(student['Birthday'])
                    if abs(student_age - age) > 2:
                        allow = False
                        print(f'GROUP {formingGroup["Id"]}: Не подходит по возрасту')
                        break
                except KeyError:
                    # print('Нет дня рождения')
                    continue
                # Проверяем подходит ли по уровню
                try:  # Берем поле дисциплины:
                    disciplines = student['Disciplines']
                    for d in disciplines:
                        if d['Discipline'] == discipline:
                            if d['Level'] not in search_levels:
                                print(f'GROUP {formingGroup["Id"]}: Не подходит по уровню')
                                allow = False
                except KeyError:
                    # print('Нет Disciplines Discipline Level')
                    continue
            if allow:
                result_groups.append(formingGroup)
                print(f'GROUP {formingGroup["Id"]}: Подходит')
        return result_groups
