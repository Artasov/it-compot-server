import datetime as dt
import re
from datetime import datetime, timedelta
from pprint import pprint

import pandas as pd

from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager


def find_header_row(df, header_name):
    for i, row in df.iterrows():
        if row[0] == header_name:
            return i
    return -1  # Возвращает -1, если заголовок не найден


def is_time_overlap(interval1, interval2):
    start1, end1 = interval1
    start2, end2 = interval2
    return max(start1, start2) < min(end1, end2)


def round_to_nearest_five(num):
    return round(num / 5) * 5


async def parse_activity(activity: str) -> dict:
    # Извлекаем временной интервал
    interval_match = re.search(r'\d{1,2}:\d{2}-\d{1,2}:\d{2}', activity)
    if interval_match:
        start_time, end_time = interval_match.group(0).split('-')
        start_time = datetime.strptime(start_time, '%H:%M')
        end_time = datetime.strptime(end_time, '%H:%M')
        start_min, end_min = (start_time.hour * 60 + start_time.minute, end_time.hour * 60 + end_time.minute)
        time_interval = [
            (datetime.min + timedelta(minutes=round_to_nearest_five(m))).time() for m in (start_min, end_min)
        ]
    else:
        time_interval = 'Временной интервал не найден'

    # Извлекаем интервал дат или одиночную дату
    date_interval_match = re.search(r'\d{1,2}\.\d{2}(?:\.\d{2,4})?(?:-\d{1,2}\.\d{2}(?:\.\d{2,4})?)?', activity)
    if date_interval_match:
        date_interval_str = date_interval_match.group(0)
        current_year = datetime.now().year

        def process_date(date_str):
            parts = date_str.split('.')

            try:
                if len(parts) == 2:  # Only day and month provided
                    date_obj = datetime.strptime(date_str + f'.{current_year}', '%d.%m.%Y')
                elif len(parts[2]) == 2:  # Two digits year provided
                    date_obj = datetime.strptime(date_str, '%d.%m.%y')
                else:  # Full year provided
                    date_obj = datetime.strptime(date_str, '%d.%m.%Y')

                # Проверяем валидность даты (например, не 30 февраля)
                date_obj.replace(year=date_obj.year)
                return date_obj
            except ValueError:
                return None

        if '-' in date_interval_str:
            start_date_str, end_date_str = date_interval_str.split('-')
            start_date = process_date(start_date_str)
            end_date = process_date(end_date_str)
            if start_date > end_date:  # If the start date is after the end date, assume the interval spans across years
                end_date = end_date.replace(year=end_date.year + 1)
        else:
            start_date = process_date(date_interval_str)
            end_date = start_date.replace(year=start_date.year + 10)  # Add 10 years to a single date

        date_interval = [start_date.date(), end_date.date()]
    else:
        date_interval = 'Интервал дат не найден'

    # Очищаем строку от временного интервала, дат, дней недели в скобках и лишних символов
    desc = re.sub(r'\d{1,2}:\d{2}-\d{1,2}:\d{2}', '', activity)  # Удаляем временной интервал
    desc = re.sub(r'\(.*?\d{1,2}\.\d{2}\.\d{2,4}.*?\)', '', desc)
    desc = re.sub(date_interval_match.group(0) if date_interval_match else '', '', desc)  # Удаляем даты
    desc = re.sub(r'\(\w{1,2}\/?\w{0,2}\/?\w{0,2}\)', '', desc)  # Удаляем дни недели в скобках
    desc = re.sub(r'\s*\-\s*', ' ', desc)  # Удаляем дефисы с окружающими пробелами
    desc = re.sub(r'\n', ' ', desc)  # Заменяем переносы строк пробелами
    desc = re.sub(r'\s{2,}', ' ', desc)  # Удаляем повторяющиеся пробелы
    desc = re.sub(r'\(\w+(?:\/\w+)*\)', '', desc)  # Удаляем дни недели в скобках(много)
    desc = desc.strip()  # Убираем пробелы в начале и конце строки

    return {
        'desc': desc,
        'time_interval': time_interval,
        'date_interval': date_interval
    }


async def parse_teachers_schedule_from_dj_mem(uploaded_file):
    teachers_schedules = []
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    # Находим строку с заголовком "Имя"
    header_row_index = find_header_row(df, "Имя")
    if header_row_index == -1:
        return "Заголовок 'Имя' не найден в первом столбце"

    teachers = list(df.iloc[header_row_index, 1:])
    # Дублируем имя преподавателя если он распределен на две колонки.
    for i, teacher in enumerate(teachers):
        if str(teacher) == 'nan':
            teachers[i] = teachers[i - 1]

    # Перебираем колонки с преподами
    for i, teacher in enumerate(teachers):
        teacher_name = teacher.split('\n')[0]

        teacher_date_line = teacher.split('\n')[1]

        date_match = re.search(r'\d{2}\.\d{2}(?:\.\d{2})?', teacher_date_line)

        if date_match:
            found_date = date_match.group(0)
            if len(found_date) == 5:  # format is dd.mm
                # Append the current year
                current_year = datetime.now().strftime("%y")
                full_date = found_date + '.' + current_year
            else:
                full_date = found_date
        else:
            full_date = 'Date not found'

        teacher_schedule_info = {
            'name': teacher_name,
            'date': datetime.strptime(full_date, '%d.%m.%y').date(),
            'activities': []
        }
        activity_list = df.iloc[2:, i + 1].dropna().tolist()
        for activity in activity_list:
            teacher_schedule_info['activities'].append(await parse_activity(activity))
        teachers_schedules.append(teacher_schedule_info)
    # pprint(teachers_schedules)
    # Объединение записей с одинаковыми именами преподавателей
    for i, ts in enumerate(teachers_schedules):
        if i == len(teachers_schedules) - 1:
            break
        if ts['name'] == teachers_schedules[i + 1]['name']:
            activities1 = ts['activities']
            activities2 = teachers_schedules[i + 1]['activities']
            s_activities = activities1 if len(activities1) < len(activities2) else activities2
            l_activities = activities2 if len(activities1) < len(activities2) else activities1
            selected_activities = []

            for activity1 in l_activities:
                is_overlap = False
                for activity2 in s_activities:
                    if is_time_overlap(activity1['time_interval'], activity2['time_interval']):
                        is_overlap = True
                        if activity1['date_interval'][0] == ts['date']:
                            selected_activities.append(activity1)
                        elif activity2['date_interval'][0] == ts['date']:
                            selected_activities.append(activity2)
                        elif 'не работаю' in activity1['desc'].lower() or \
                                'в другом месте' in activity1['desc'].lower():
                            selected_activities.append(activity2)
                        elif 'не работаю' in activity2['desc'].lower() or \
                                'в другом месте' in activity2['desc'].lower():
                            selected_activities.append(activity1)
                        break

                if not is_overlap:
                    selected_activities.append(activity1)

            ts['activities'] = selected_activities
            teachers_schedules[i] = ts
            del teachers_schedules[i + 1]

    # pprint(teachers_schedules)

    working_teachers = teachers_schedules

    all_teachers = await CustomHHApiV2Manager().getActiveTeachersShortNames()  # Все имена преподаватели
    # pprint(all_teachers)
    # for teacher in working_teachers:
    #     pprint(teacher)
    # Добавим преподавателей не работающих в этот день и проставим занятость 'Выходной'
    for teacher in all_teachers:
        if not any(w_teacher['name'].lower() == teacher.lower() for w_teacher in working_teachers):
            working_teachers.append({
                'name': teacher,
                'date': working_teachers[0]['date'],
                'activities': [{
                    'desc': 'Выходной',
                    'time_interval': [datetime.strptime('00:00', '%H:%M').time(),
                                      datetime.strptime('23:59', '%H:%M').time()],
                    'date_interval': [working_teachers[0]['date']]
                }]
            })

    # Форматируем активность.
    for i in range(len(working_teachers)):
        for j in range(len(working_teachers[i]['activities'])):
            if 'выходной' in working_teachers[i]['activities'][j]['desc'].lower():
                continue
            if 'не работаю' in working_teachers[i]['activities'][j]['desc'].lower() or \
                    'в другом месте' in working_teachers[i]['activities'][j]['desc'].lower():
                working_teachers[i]['activities'][j]['desc'] = 'Не работает'
            else:
                working_teachers[i]['activities'][j]['desc'] = 'Урок'

    # Удаляем ненужных преподавателей
    result = []
    for teacher in working_teachers:
        if 'Соболев Ф'.lower() in teacher['name'].lower() or \
                'Каретников А'.lower() in teacher['name'].lower() or \
                'Войнов Ф'.lower() in teacher['name'].lower() or \
                'Комлев Ф'.lower() in teacher['name'].lower() or \
                'Тест '.lower() in teacher['name'].lower() or \
                'Тесттт'.lower() in teacher['name'].lower() or \
                'Драганюк О'.lower() in teacher['name'].lower() or \
                'Борисенко П'.lower() in teacher['name'].lower() or \
                'Соловьева А'.lower() in teacher['name'].lower() or \
                'Дудкин Д'.lower() in teacher['name'].lower() or \
                'Кирякова К'.lower() in teacher['name'].lower() or \
                'Костылева Ю'.lower() in teacher['name'].lower() or \
                'Кочерова Т'.lower() in teacher['name'].lower() or \
                'Николаева Л'.lower() in teacher['name'].lower() or \
                'Техперерыв'.lower() in teacher['name'].lower() or \
                'Чернышева Т'.lower() in teacher['name'].lower():
            continue
        result.append(teacher)

    return result


async def fill_schedule(activities, date):
    pprint(date)
    pprint(activities)
    full_day_schedule = []
    is_weekend = date.weekday() >= 5
    if is_weekend:
        start_of_day = dt.datetime.combine(date, dt.time(9, 0))  # 09:00 на выходных
        end_of_day = dt.datetime.combine(date, dt.time(21, 0))  # 21:00 всегда
    else:
        start_of_day = dt.datetime.combine(date, dt.time(15, 0))  # 15:00 в будни
        end_of_day = dt.datetime.combine(date, dt.time(21, 0))  # 21:00 всегда

    current_time = start_of_day

    while current_time <= end_of_day:
        full_day_schedule.append({
            'Начало интервала': current_time.strftime('%H:%M'),
            'Конец интервала': (current_time + timedelta(minutes=5)).strftime('%H:%M'),
            'Занятость': 'Не указано'
        })
        current_time += timedelta(minutes=5)

    for activity in activities:
        start_time = dt.datetime.combine(date, activity['time_interval'][0])
        # Проверка на интервал через полночь
        if activity['time_interval'][1] == dt.time(0, 0):
            end_time = dt.datetime.combine(date, dt.time(23, 55))
        else:
            end_time = dt.datetime.combine(date, activity['time_interval'][1])

        while start_time < end_time:
            interval_start_str = start_time.strftime('%H:%M')
            for interval in full_day_schedule:
                if interval['Начало интервала'] == interval_start_str:
                    interval['Занятость'] = activity['desc']
                    break
            start_time += timedelta(minutes=5)

    return full_day_schedule


async def create_schedule(teachers_activities):
    schedule_list = []
    for teacher in teachers_activities:
        # if 'Паршикова' not in teacher['name']:
        #     continue
        teacher_schedule = await fill_schedule(teacher['activities'], teacher['date'])

        for entry in teacher_schedule:
            schedule_list.append([
                teacher['name'],  # Имя учителя
                entry['Начало интервала'],
                entry['Конец интервала'],
                entry['Занятость']
            ])
    schedule_df = pd.DataFrame(schedule_list)
    headers = ['Имя', 'Начало интервала', 'Конец интервала', 'Занятость']
    schedule_df.loc[-1] = headers  # Добавляем заголовки в начало DataFrame
    schedule_df.index = schedule_df.index + 1  # Сдвигаем индекс
    schedule_df.sort_index(inplace=True)  # Сортируем индекс
    return schedule_df
