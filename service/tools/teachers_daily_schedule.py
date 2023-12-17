from pprint import pprint

import pandas as pd
import datetime as dt
import re
from datetime import timedelta

from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager


def find_header_row(df, header_name):
    for i, row in df.iterrows():
        if row[0] == header_name:
            return i
    return -1


def parse_teachers_schedule_from_dj_mem(uploaded_file):
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    header_row_index = find_header_row(df, "Имя")
    if header_row_index == -1:
        return "Заголовок 'Имя' не найден в первом столбце"

    teachers_schedule = {}
    all_teachers = CustomHHApiV2Manager().get_short_names_teachers()

    teachers = df.iloc[header_row_index, 1:].dropna()
    for teacher in all_teachers:
        if not any(teacher in t for t in teachers):
            teachers_schedule[teacher] = ['Выходной']

    for index, row in df.iterrows():
        if index < 2:
            continue

        for i, teacher in enumerate(teachers):
            col_index = i + 1
            cell_value = row[col_index]

            if pd.notna(cell_value) and not isinstance(cell_value, dt.time):
                teacher_key = ' '.join(teacher.replace('\n', ' ').strip().split()[:3])
                teacher_key = re.sub(r'[\(\)\d]', '', teacher_key).strip()

                if teacher_key == 'Имя':
                    continue

                # Находим соответствующий ключ в teachers_schedule
                matched_key = next((key for key in teachers_schedule if key.lower() == teacher_key.lower()), None)
                if matched_key is not None:
                    teachers_schedule[matched_key].append(str(cell_value))
                else:
                    teachers_schedule[teacher_key] = [str(cell_value)]

    return teachers_schedule


def parse_time_activity(activity_str):
    match = re.search(r'([^\d\n]+)?(\d{1,2}:\d{2})-(\d{1,2}:\d{2})', activity_str)
    if match:
        description = match.group(1).strip() if match.group(1) else 'Не указано'
        start_time = dt.datetime.strptime(match.group(2), '%H:%M')
        end_time = dt.datetime.strptime(match.group(3), '%H:%M')
        description = re.sub(r'\n.*', '', description).strip()
        return start_time, end_time, description
    else:
        raise ValueError(f'Cannot parse the activity string: {activity_str}')


def fill_schedule(activities):
    full_day_schedule = []
    start_of_day = dt.datetime.strptime('00:00', '%H:%M')
    end_of_day = dt.datetime.strptime('23:55', '%H:%M')
    current_time = start_of_day

    while current_time <= end_of_day:
        full_day_schedule.append({
            'Начало интервала': current_time.strftime('%H:%M'),
            'Конец интервала': (current_time + timedelta(minutes=5)).strftime('%H:%M'),
            'Занятость': 'Пусто'
        })
        current_time += timedelta(minutes=5)

    for activity in activities:
        if activity == 'Выходной':
            for interval in full_day_schedule:
                interval['Занятость'] = 'Выходной'
        else:
            start_time, end_time, description = parse_time_activity(activity)
            while start_time < end_time:
                interval_start_str = start_time.strftime('%H:%M')
                interval_end_str = (start_time + timedelta(minutes=5)).strftime('%H:%M')

                for interval in full_day_schedule:
                    if interval['Начало интервала'] == interval_start_str:
                        interval['Занятость'] = description
                        break
                start_time += timedelta(minutes=5)

    return full_day_schedule


def create_schedule(teachers_activities):
    schedule_list = []

    for teacher, activities in teachers_activities.items():
        teacher_schedule = fill_schedule(activities)
        for entry in teacher_schedule:
            schedule_list.append([
                teacher.split('\n')[0],
                entry['Начало интервала'],
                entry['Конец интервала'],
                entry['Занятость']
            ])

    schedule_df = pd.DataFrame(schedule_list)
    headers = ['Имя', 'Начало интервала', 'Конец интервала', 'Занятость']
    schedule_df.loc[-1] = headers
    schedule_df.index = schedule_df.index + 1
    schedule_df.sort_index(inplace=True)

    return schedule_df
