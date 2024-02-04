import traceback

import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render

from Core.error_messages import TEACHER_EMAIL_NOT_FOUND
from Core.services.common import acontroller
from service.hollihop.classes.exeptions import TeacherNotFound
from service.hollihop.funcs.teachers_salary import get_teacher_salary_by_email
from service.tools.gsheet.classes.gsheetsclient import GSheetsClient, ListAlreadyExists
from service.tools.teachers_daily_schedule import create_schedule, \
    parse_teachers_schedule_from_dj_mem
from tools.forms.other import LoadHHTeachersScheduleXLSXForm
from tools.forms.teachers_salary import GetTeacherSalaryForm

"""
 'Информатика Junior (Scratch + компьютерная грамотность)',
 'Программирование Scratch + математика',
 'Город программистов Джуниор',
 'Город программистов',
 'Python GameDev (Разработка 2D-игр 1 ступень)',
 'Python GameDev (Разработка 2D и 3D-игр 2 ступень)',
 'Программирование Python (начальный уровень)',
 'Программирование Python не игры',
 'Web-программирование (1 ступень frontend)',
 'Web-программирование (2 ступень backend)',
 'Web-дизайн',
 'Графический дизайн Junior',
 'Графический дизайн',
 'Медиа вне программы',
 'Школа блогеров',
 '3D-моделирование (Blender)',
 '3D-моделирование 2 год',
 'Программирование вне программы',
 'Внутренние мероприятия',
 'Хакатон',
 'Марафон IT-профессий',
 '(ОУ) Scratch программирование',
 '(ОУ) Python программирование',
 '(ОУ) Школа блогеров / дизайн',
 '(ОУ) Веб-программирование',
 '(ОУ) 3D-моделирование',
 '(ОУ) Дизайн',
 '(ОУ) Школа блогера',
 '(ОУ) Информатика Junior',
 '(ОУ) Программирование (разработка сайтов или игр)',
 '(ОУ) Web-дизайн',
 '(ОУ) вне программы',
 'Клуб',
 'Программирование Roblox',
 'Архив не могу удалить (',
 '(архив, не могу удалить)',
 '(ОУ) Марафон профессий (удалить)',
 'Разработка чат-ботов',
 '(0)Разработка приложений на Пайтон',
 'Разработка мобильных приложений на Python для Android',
 'Мастер анимации - создаем мультфильмы',
 'Разработка мобильных приложений для Android в App Inventor',
 'Первые шаги в программировании и английском.  джуниор',
 'Первые шаги в 3д-моделировании.  Создай свой мир майнкрафта',
 'Видеомонтаж на компьютере - прокачка навыков',
 'Академия Заработка',
 'Урок диагностика',
 'Нейросети'
"""
"""
Easy
Easy-medium
Medium
Medium-hard
Hard
Very hard
"""


@acontroller('Страница для записи на вводный модуль')
async def join_to_group(request) -> HttpResponse:
    return render(request, 'tools/join_to_group.html', {
        'theme': 'light'
    })


@acontroller('Интервальная выгрузка занятости преподавателей за день из .xlsx')
async def parse_teachers_schedule_ui(request) -> HttpResponse:
    context = {}
    if request.method == 'POST':
        form = LoadHHTeachersScheduleXLSXForm(request.POST, request.FILES)
        if form.is_valid():
            teachers_schedule_xlsx = form.cleaned_data['file']
            gdoc_id = form.cleaned_data['gdoc_id']
            new_glist_name = form.cleaned_data['new_glist_name'].replace('.', '_').replace(':', '_')
            try:
                teachers_parsed_schedule = parse_teachers_schedule_from_dj_mem(teachers_schedule_xlsx)
                schedule_dataframe = create_schedule(teachers_parsed_schedule)
                client = GSheetsClient(gdoc_id)

                # Создаем новый лист
                client.create_list(new_glist_name)

                # Обновляем данные на новом листе
                range_name = f'{new_glist_name}!A1'
                client.update_list_with_df(range_name, schedule_dataframe)
                context['success'] = '  Готово, проверьте таблицу'
            except ListAlreadyExists as e:
                form.add_error(None, f'List with this name \'{new_glist_name}\' already exists, delete or rename.')
            except Exception as e:
                traceback_str = ''.join(traceback.format_tb(e.__traceback__))
                form.add_error(None,
                               f'Произошла ошибка при загрузке данных: '
                               f'{e}\n\nTraceback:\b{traceback_str}')
    else:
        form = LoadHHTeachersScheduleXLSXForm()

    context['form'] = form
    return render(request, 'tools/parse_teachers_schedule.html', context)


@acontroller('Отображение зарплаты учителя по email & unipass')
async def teacher_salary(request) -> HttpResponse:
    form = GetTeacherSalaryForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data['email']
        try:
            teacher_month_lessons_rows = get_teacher_salary_by_email(email)
            teacher_month_lessons = []
            for info in teacher_month_lessons_rows:
                if len(info) < 2:
                    info = info[0]
                teacher_month_lessons.append({
                    'gid': info[0],  # id группы
                    'title': info[1],  # название
                    'discipline': info[2],
                    'level': info[3],  # Уровень ученика
                    'type': info[4],
                    'student': info[5],  # Ученик
                    'date': info[6],
                    'skip': info[7],
                    'duration': info[8],
                    'start_date': info[9],
                    'end_date': info[10],
                    'teacher': info[11],
                    'money': info[12],
                })

            # Преобразование списка словарей в DataFrame
            teacher_month_lessons_df = pd.DataFrame(teacher_month_lessons)
            # Преобразование значений 'duration' в числовой формат
            teacher_month_lessons_df['duration'] = pd.to_numeric(teacher_month_lessons_df['duration'], errors='coerce')
            # Группировка данных по 'gid', 'date', 'discipline', 'type'
            grouped_lessons = teacher_month_lessons_df.groupby(['gid', 'date', 'discipline', 'type'])
            # Фильтрация групп, где не у всех уроков одновременно skip == 'TRUE' и duration == 0
            filtered_lessons = grouped_lessons.filter(
                lambda x: not ((x['skip'] == 'TRUE') & (x['duration'] == 0)).all())
            # Если нужно вернуть данные в исходный формат списка словарей
            teacher_month_lessons = filtered_lessons.to_dict('records')

            sum_salary = 0
            for i, tl in enumerate(teacher_month_lessons):
                if i == 0:
                    continue
                try:
                    sum_salary += int(tl['money'])
                except ValueError:
                    pass

            return render(request, 'tools/teachers_salary_result.html', {
                'teacher_month_lessons_list': teacher_month_lessons,
                'sum_salary': sum_salary,
                'email': email
            })
        except TeacherNotFound:
            form.add_error(None, TEACHER_EMAIL_NOT_FOUND)
    return render(request, 'tools/teachers_salary.html', {'form': form})
