from itertools import islice
from typing import Any, Dict

import pandas as pd
import datetime as dt

import re
from datetime import datetime, timedelta


def read_xlsx(file_path):
    """
    Читает .xlsx файл и возвращает его содержимое в виде pandas DataFrame.

    :param file_path: Путь к файлу .xlsx
    :return: pandas DataFrame с содержимым файла
    """
    try:
        data = pd.read_excel(file_path, engine='openpyxl')
        return data
    except Exception as e:
        return f"Ошибка при чтении файла: {e}"


def find_header_row(df, header_name):
    for i, row in df.iterrows():
        if row[0] == header_name:
            return i
    return -1  # Возвращает -1, если заголовок не найден


def parse_teachers_schedule_from_dj_mem(uploaded_file):
    df = pd.read_excel(uploaded_file, engine='openpyxl')

    # Находим строку с заголовком "Имя"
    header_row_index = find_header_row(df, "Имя")
    if header_row_index == -1:
        return "Заголовок 'Имя' не найден в первом столбце"

    teachers_schedule = {}

    # Используем найденную строку для извлечения имен преподавателей
    teachers = df.iloc[header_row_index, 1:].dropna()
    print(teachers)

    for index, row in df.iterrows():
        if index < 2:
            continue

        for i, teacher in enumerate(teachers):
            col_index = i + 1
            cell_value = row[col_index]

            if pd.notna(cell_value) and not isinstance(cell_value, dt.time):
                teacher_key = teacher.replace('\n', ' ').strip()
                if teacher_key not in teachers_schedule:
                    teachers_schedule[teacher_key] = []
                teachers_schedule[teacher_key].append(str(cell_value))

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
            'Начало интервала': current_time.strftime('%H:%M'),  # Преобразуем объект time в строку
            'Конец интервала': (current_time + timedelta(minutes=5)).strftime('%H:%M'),  # Аналогично
            'Занятость': 'Пусто'
        })
        current_time += timedelta(minutes=5)

    for activity in activities:
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
    # Создаем список для данных расписания
    schedule_list = []

    for teacher, activities in teachers_activities.items():
        teacher_schedule = fill_schedule(activities)
        for entry in teacher_schedule:
            schedule_list.append([
                teacher.split('\n')[0],  # Имя учителя
                entry['Начало интервала'],
                entry['Конец интервала'],
                entry['Занятость']
            ])

    # Создаем DataFrame без указания заголовков столбцов
    schedule_df = pd.DataFrame(schedule_list)

    # Вставляем заголовки как первую строку данных
    headers = ['Имя', 'Начало интервала', 'Конец интервала', 'Занятость']
    schedule_df.loc[-1] = headers  # Добавляем заголовки в начало DataFrame
    schedule_df.index = schedule_df.index + 1  # Сдвигаем индекс
    schedule_df.sort_index(inplace=True)  # Сортируем индекс

    return schedule_df
