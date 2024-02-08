import asyncio
import logging
from urllib.parse import urlencode

import aiohttp as aiohttp
from django.conf import settings

log = logging.getLogger('base')


class HolliHopApiV2Manager:
    def __init__(self, domain: str = settings.HOLLIHOP_DOMAIN, authkey: str = settings.HOLLIHOP_AUTHKEY):
        if not all((domain, authkey)):
            raise ValueError('domain and authkey required')
        self.domain = domain
        self.authkey = authkey

    async def get_teachers(self, **kwargs):
        teachers = await self.api_call('GetTeachers', **kwargs)
        return teachers.get('Teachers', [])

    @staticmethod
    async def fetch(session, url):
        async with session.get(url) as response:
            result = await response.json()
            return result

    async def fetch_all(self, url, params, maxTake=10000, batchSize=1000):
        # async with aiohttp.ClientSession(trust_env=True, connector=TCPConnector(limit_per_host=5, ssl=False)) as session:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for skip in range(0, maxTake, batchSize):
                batch_params = params.copy()
                batch_params['skip'] = skip
                batch_params['take'] = min(1000, maxTake - skip)
                batch_url = f"{url}?{urlencode(batch_params, safe='/', encoding='utf-8')}"
                tasks.append(self.fetch(session, batch_url))

            results = await asyncio.gather(*tasks)
            return results

    async def api_call_pagination(self, endpoint, **params):
        url = f"https://{self.domain}/Api/V2/{endpoint}"
        params['authkey'] = self.authkey
        return await self.fetch_all(url, params)

    async def api_call(self, endpoint, **params):
        url = f"https://{self.domain}/Api/V2/{endpoint}"
        params['authkey'] = self.authkey
        async with aiohttp.ClientSession() as session:
            response = await self.fetch(session, f"{url}?{urlencode(params)}")
            return response

    @staticmethod
    async def post_fetch(session, url, data):
        async with session.post(url, json=data) as response:
            json = await response.json()
            if response.status == 200:
                return {'success': True}
            else:
                return {'success': False}

    async def api_post_call(self, endpoint, **params):
        url = f"https://{self.domain}/Api/V2/{endpoint}"
        params['authkey'] = self.authkey
        async with aiohttp.ClientSession() as session:
            response = await self.post_fetch(session, url, params)
            return response

    async def add_ed_unit_student(self, **kwargs):
        required_params = ['edUnitId', 'studentClientId']
        if not all(param in kwargs for param in required_params):
            raise ValueError(f"Missing required parameters: {', '.join(required_params)}")
        response = await self.api_post_call('AddEdUnitStudent', **kwargs)
        return response

    async def get_disciplines(self, **kwargs):
        disciplines = await self.api_call('GetDisciplines', **kwargs)
        return disciplines.get('Disciplines', [])

    async def get_levels(self, **kwargs):
        disciplines = await self.api_call('GetLevels', **kwargs)
        return disciplines.get('Levels', [])

    async def get_students(self, **kwargs):
        students = await self.api_call('GetStudents', **kwargs)
        students = students.get('Students', [])
        return students if students else []
        # {'AddressDate': '2022-10-01',
        #  'Agents': [{'EMail': '1@2.ru',
        #              'FirstName': 'Мама',
        #              'IsCustomer': False,
        #              'LastName': 'Котова',
        #              'Mobile': '80000000000',
        #              'UseEMailBySystem': True,
        #              'UseMobileBySystem': True,
        #              'WhoIs': 'Мама'}],
        #  'Assignees': [{'FullName': 'Богданова Виктория Витальевна', 'Id': 334}],
        #  'Birthday': '2013-10-12',
        #  'ClientId': 9,
        #  'Created': '2022-10-01T16:10:47',
        #  'Disciplines': [{'Discipline': 'Информатика Junior (Scratch компьютерная '
        #                                 'грамотность)',
        #                   'Level': 'Medium'},
        #                  {'Discipline': 'Scratch математика'},
        #                  {'Discipline': 'Клуб'}],
        #  'EMail': '1@1.ru',
        #  'ExtraFields': [{'Name': 'Часовой пояс UTC',
        #                   'Value': 'UTC 0 (По гринвичу Мск-3)'},
        #                  {'Name': 'Комментарий педагога после ОУ',
        #                   'Value': 'Интересовался курсом программирования, любит '
        #                            'Minecraft'},
        #                  {'Name': 'id ученика', 'Value': '12345678'},
        #                  {'Name': 'Причина прогула',
        #                   'Value': 'ТП: проблемы со звуком,видео'},
        #                  {'Name': 'Антитренинги (логин)', 'Value': '1@mai.ru'},
        #                  {'Name': 'Ссылка на Мой класс', 'Value': 'https://'},
        #                  {'Name': 'Ссылка на amoCRM', 'Value': 'https://'},
        #                  {'Name': 'Scratch (логин, пароль)', 'Value': 'it-1  35666'}],
        #  'FirstName': 'Кот',
        #  'Gender': True,
        #  'Id': 3431,
        #  'LastName': 'Котов',
        #  'LearningTypes': ['Вводный модуль курса (russian language)',
        #                    'Занятия в микро-группах (russian language)',
        #                    'Клуб'],
        #  'Maturity': 'Младше-школьники (7-10 лет)',
        #  'MiddleName': 'Компотович',
        #  'Mobile': '80000000000',
        #  'OfficesAndCompanies': [{'Id': 1, 'Name': 'Занятия (Zoom2)'},
        #                          {'Id': 4, 'Name': 'Клуб IT-Компот'},
        #                          {'Id': 5, 'Name': 'Занятия (Zoom3)'},
        #                          {'Id': 9, 'Name': 'Занятия (zoom4)'},
        #                          {'Id': 10, 'Name': 'Занятия (Zoom5)'}],
        #  'PhotoUrls': ['/Files/it-school.t8s.ru/Photos/3hexvkyg.rhv-100x100.jpg',
        #                '/Files/it-school.t8s.ru/Photos/3hexvkyg.rhv-150x150.jpg',
        #                '/Files/it-school.t8s.ru/Photos/3hexvkyg.rhv-150x180.jpg',
        #                '/Files/it-school.t8s.ru/Photos/Originals/3hexvkyg.rhv.png'],
        #  'SocialNetworkPage': 'vk.com/',
        #  'Status': 'Закончил обучение',
        #  'StatusId': 3,
        #  'Updated': '2023-12-05T02:05:59',
        #  'UseEMailBySystem': True,
        #  'UseMobileBySystem': True}

    async def get_students_by_ids(self, ids: tuple | list):
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_student_by_id(session, student_id) for student_id in ids]
            students = await asyncio.gather(*tasks)
        return [student[0] for student in students if student]

    async def get_student_by_id(self, session, student_id):
        student_data = await self.get_students(clientId=str(student_id), session=session)
        return student_data

    async def get_ed_unit_student(self, **kwargs):
        student_units = await self.api_call('GetEdUnitStudents', **kwargs)
        return student_units.get('EdUnitStudents', [])

    async def get_ed_units(self, **kwargs):
        edUnits = await self.api_call_pagination('GetEdUnits', **kwargs)
        result_list = []
        for result in edUnits:

            try:
                values_list = result['EdUnits']
            except KeyError as e:
                log.error(f'Traceback \n{e}\n\n{edUnits})')
                if len(edUnits) != 0:
                    if edUnits[0].get('Error', False):
                        log.error(edUnits[0].get('Error'))
                        raise PermissionError(edUnits[0].get('Error') + '. API LIMIT')
                raise KeyError(e)

            for value in values_list:
                result_list.append(value)
        result_filtered = []
        for result in result_list:
            if int(result['Id']) in [int(value['Id']) for value in result_filtered]:
                continue
            result_filtered.append(result)
        return result_filtered
        # [
        #     {
        #         'Corporative': False,
        #         'Discipline': 'Город программистов Джуниор',
        #         'Id': 13492,
        #         'LearningType': 'Занятия в микро-группах (russian language)',
        #         'Level': 'Easy',
        #         'Name': 'SCR-2-GROUP начало',
        #         'OfficeOrCompanyAddress': 'https://us06web.zoom.us/j/86814523112?pwd=aG90SWVOUmJweENqbzVJUzAvTzh0UT09  '
        #                                   'Идентификатор конференции: 868 1452 3112 Код '
        #                                   'доступа: 2146648',
        #         'OfficeOrCompanyId': 10,
        #         'OfficeOrCompanyName': 'Занятия (Zoom5)',
        #         'OfficeTimeZone': '+03:00',
        #         'ScheduleItems': [
        #             {
        #                 'BeginDate': '2023-09-11',
        #                 'BeginTime': '17:50',
        #                 'ClassroomId': 103,
        #                 'ClassroomLink': 'https://us06web.zoom.us/j/86814523112?pwd=aG90SWVOUmJweENqbzVJUzAvTzh0UT09',
        #                 'ClassroomName': 'Зум 5 (ауд13)',
        #                 'EndDate': '2024-05-20',
        #                 'EndTime': '19:20',
        #                 'Id': 76963,
        #                 'Teacher': 'Волошин Матвей Петрович',
        #                 'TeacherGenders': [True],
        #                 'TeacherId': 453,
        #                 'TeacherIds': [453],
        #                 'TeacherPhotoUrls': [None],
        #                 'Teachers': ['Волошин Матвей Петрович'],
        #                 'Weekdays': 1
        #             }
        #         ],
        #         'StudentsCount': 10,
        #         'StudyUnitsInRange': '32 а.ч.',
        #         'Type': 'Group',
        #         'Vacancies': 1
        #     },
        #     {...},
        #     {...},
        # ]

    async def get_ed_unit_students(self, **kwargs):
        ed_unit_students = await self.api_call_pagination('GetEdUnitStudents', **kwargs)
        result_list = []
        for result in ed_unit_students:
            values_list = result['EdUnitStudents']
            for value in values_list:
                result_list.append(value)
        return result_list
        # RETURNED
        # [
        #     {
        #         'BeginDate': '2022-10-01',
        #         'BeginTime': '09:00',
        #         'EdUnitCorporative': False,
        #         'EdUnitDiscipline': 'Информатика Junior (Scratch + компьютерная грамотность)',
        #         'EdUnitId': 1227,
        #         'EdUnitLearningType': 'Вводный модуль курса (russian language)',
        #         'EdUnitLevel': 'Medium',
        #         'EdUnitName': 'JUNIOR-ВASE-M',
        #         'EdUnitOfficeOrCompanyId': 1,
        #         'EdUnitOfficeOrCompanyName': 'Занятия (Zoom2)',
        #         'EdUnitType': 'Group',
        #         'EndDate': '2022-10-10',
        #         'EndTime': '10:30',
        #         'Status': 'Normal',
        #         'StudentAgents': [
        #             {
        #                 'EMail': 'oksana.soldatova.1988@mail.ru',
        #                 'FirstName': 'Солдатов',
        #                 'IsCustomer': True,
        #                 'LastName': 'Николаевич',
        #                 'MiddleName': 'Кирилл',
        #                 'Mobile': '+79279754223',
        #                 'UseEMailBySystem': True,
        #                 'UseMobileBySystem': True,
        #                 'WhoIs': 'Родитель'
        #             }
        #         ],
        #         'StudentClientId': 166,
        #         'StudentExtraFields': [
        #             {
        #                 'Name': 'id ученика',
        #                 'Value': '20355449'
        #             },
        #             {
        #                 'Name': 'Особые примечания по ученику/лиду',
        #                 'Value': 'Особые примечания'
        #             }
        #         ],
        #         'StudentMobile': '+79046661630',
        #         'StudentName': 'Кирилл Николаевич Солдатов',
        #         'StudyMinutes': 180.0,
        #         'StudyUnits': '4 а.ч.',
        #         'Weekdays': 1
        #     },
        #     {...},
        #     {...},
        # ]
