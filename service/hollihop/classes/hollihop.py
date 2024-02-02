import asyncio
from pprint import pprint

import aiohttp as aiohttp
import requests
from requests import HTTPError, RequestException
from urllib.parse import urlencode

from config.settings import HOLLIHOP_DOMAIN, HOLLIHOP_AUTHKEY


class HolliHopApiV2Manager:
    def __init__(self, domain: str = HOLLIHOP_DOMAIN, authkey: str = HOLLIHOP_AUTHKEY):
        self.domain = domain
        self.authkey = authkey

    async def getTeachers(self, **kwargs):
        teachers = await self.api_call('GetTeachers', **kwargs)
        return teachers.get('Teachers', [])

    @staticmethod
    async def fetch(session, url):
        async with session.get(url) as response:
            return await response.json()

    async def fetch_all(self, url, params, maxTake=10000, batchSize=1000):
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
        print("#################")
        print(f'{self.authkey=}')
        return await self.fetch_all(url, params)

    async def api_call(self, endpoint, **params):
        url = f"https://{self.domain}/Api/V2/{endpoint}"
        params['authkey'] = self.authkey
        async with aiohttp.ClientSession() as session:
            response = await self.fetch(session, f"{url}?{urlencode(params)}")
            return response

    async def getDisciplines(self, **kwargs):
        disciplines = await self.api_call('GetDisciplines', **kwargs)
        return disciplines.get('Disciplines', [])

    async def getLevels(self, **kwargs):
        disciplines = await self.api_call('GetLevels', **kwargs)
        return disciplines.get('Levels', [])

    async def getStudent(self, **kwargs):
        students = await self.api_call('GetStudents', **kwargs)
        return students.get('Students', [[]])[0]

    async def getEdUnitStudent(self, **kwargs):
        studentUnits = await self.api_call('GetEdUnitStudents', **kwargs)
        return studentUnits.get('EdUnitStudents', [])

    async def getStudentsByIds(self, ids: list[int, ...] | tuple[int, ...]):
        if len(ids) == 0: return []
        tasks = [self.getStudent(clientId=id) for id in ids]
        results = await asyncio.gather(*tasks)
        return [item for item in results if item]
        # [
        #     {
        #         'AddressDate': '2022-11-21',
        #         'Agents': [{
        #             'EMail': 'bezrukovaov@mail.ru',
        #             'FirstName': 'Радченко',
        #             'IsCustomer': True,
        #             'LastName': 'Васильевна',
        #             'MiddleName': 'Ольга',
        #             'Mobile': '+79121378820',
        #             'UseEMailBySystem': True,
        #             'UseMobileBySystem': True,
        #             'WhoIs': 'Родитель'
        #         }],
        #         'Birthday': '2013-09-03',
        #         'ClientId': 2031,
        #         'Created': '2022-11-21T17:47:33',
        #         'Disciplines': [
        #             {'Discipline': 'Программирование Scratch + математика',
        #              'Level': 'Easy-medium'},
        #             {'Discipline': 'Хакатон'},
        #             {'Discipline': 'Город программистов Джуниор',
        #              'Level': 'Easy-medium'}
        #         ],
        #         'ExtraFields': [
        #             {'Name': 'id ученика', 'Value': '21327965'},
        #             {'Name': 'Ссылка на amoCRM',
        #              'Value': 'https://itbestonlineschool.amocrm.ru/leads/detail/24384061'},
        #             {'Name': 'Ссылка на Мой класс',
        #              'Value': 'https://app.moyklass.com/user/3154720/joins'},
        #             {'Name': 'Антитренинги (логин)',
        #              'Value': 'bezrukovaov@mail.ru'},
        #             {'Name': 'Scratch (логин, пароль)',
        #              'Value': 'it-alex-rad 2146648'},
        #             {'Name': 'Филиал', 'Value': 'IT-Компот'}
        #         ],
        #         'FirstName': 'Александр',
        #         'Gender': True,
        #         'Id': 7508,
        #         'LastName': 'Радченко',
        #         'LearningTypes': [
        #             'Вводный модуль курса (russian language)',
        #             'Занятия в микро-группах (russian language)',
        #             'Мероприятия'
        #         ],
        #         'MiddleName': 'Константинович',
        #         'Mobile': '+79121683185',
        #         'OfficesAndCompanies': [
        #             {'Id': 1, 'Name': 'Занятия (Zoom2)'},
        #             {'Id': 2, 'Name': 'Открытые уроки'},
        #             {'Id': 4, 'Name': 'Клуб IT-Компот'},
        #             {'Id': 5, 'Name': 'Занятия (Zoom3)'},
        #             {'Id': 7, 'Name': 'Корпоративный Zoom'},
        #             {'Id': 8, 'Name': 'Занятия личный Zoom'},
        #             {'Id': 9, 'Name': 'Занятия (zoom4)'},
        #             {'Id': 10, 'Name': 'Занятия (Zoom5)'}
        #         ],
        #         'Status': 'Закончил обучение',
        #         'StatusId': 3,
        #         'Updated': '2023-11-18T17:43:11',
        #         'UseEMailBySystem': True,
        #         'UseMobileBySystem': True
        #     },
        #     {...},
        #     {...},
        # ]

    async def getEdUnitStudentsByUnitId(self, ids: list[int, ...] | tuple[int, ...]):
        tasks = [self.getEdUnitStudent(edUnitId=id) for id in ids]
        results = await asyncio.gather(*tasks)
        return [item for sublist in results if sublist for item in sublist]

    async def getEdUnits(self, **kwargs):
        edUnits = await self.api_call_pagination('GetEdUnits', **kwargs)
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print(edUnits)
        result_list = []
        for result in edUnits:
            values_list = result['EdUnits']
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

    async def getEdUnitStudents(self, **kwargs):
        edUnitStudents = await self.api_call_pagination('GetEdUnitStudents', **kwargs)
        result_list = []
        for result in edUnitStudents:
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

    async def getStudents(self, **kwargs):
        edUnitStudents = await self.api_call_pagination('GetStudents', **kwargs)
        result_list = []
        for result in edUnitStudents:
            values_list = result['Students']
            for value in values_list:
                result_list.append(value)
        return result_list
