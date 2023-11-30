from datetime import datetime

import pandas as pd
from django.conf import settings
from django.shortcuts import render

from Core.error_messages import TEACHER_EMAIL_NOT_FOUND
from service.hollihop.classes.exeptions import TeacherNotFound
from service.hollihop.funcs.teachers_salary import get_teacher_salary_by_email
from service.tools.gsheet.classes.gsheetsclient import GSheetsClient
from service.tools.techers_daily_schedule import create_schedule, \
    parse_teachers_schedule_from_dj_mem

from tools.forms.other import LoadHHTeachersScheduleXLSXForm
from tools.forms.teachers_salary import GetTeacherSalaryForm


def parse_teachers_schedule_ui(request):
    context = {}
    if request.method == 'POST':
        form = LoadHHTeachersScheduleXLSXForm(request.POST, request.FILES)
        if form.is_valid():
            teachers_schedule_xlsx = form.cleaned_data['file']
            gsheet_id = form.cleaned_data['gsheet_id']
            try:
                teachers_activities = parse_teachers_schedule_from_dj_mem(teachers_schedule_xlsx)
                schedule_dataframe = create_schedule(teachers_activities)

                # Добавляем строку с датой выгрузки перед заголовками
                current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                date_row = [f'Дата выгрузки: {current_date}'] + [''] * (len(schedule_dataframe.columns) - 1)

                # Добавляем строку с датой выгрузки в DataFrame
                date_df = pd.DataFrame([date_row], columns=schedule_dataframe.columns)
                schedule_dataframe = pd.concat([date_df, schedule_dataframe], ignore_index=True)

                client = GSheetsClient(
                    settings.GOOGLE_API_JSON_CREDS_PATH,
                    gsheet_id
                )

                # Получение первого листа
                sheets_titles = client.get_sheets_titles()
                if not sheets_titles:
                    raise ValueError("Документ не содержит ни одного листа.")
                first_sheet_title = sheets_titles[0]
                range_name = f'{first_sheet_title}!A1'

                response = client.update_sheet_with_df(range_name, schedule_dataframe)
                context['success'] = 'Готово, проверьте таблицу'
            except Exception as e:
                form.add_error(None, f'Произошла ошибка при загрузке данных: {e}')
    else:
        form = LoadHHTeachersScheduleXLSXForm()

    context['form'] = form
    return render(request, 'tools/parse_teachers_schedule.html', context)



def teacher_salary(request):
    form = GetTeacherSalaryForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data['email']
        try:
            teacher_salary_rows = get_teacher_salary_by_email(email)
            sum_salary = 0
            for i, row in enumerate(teacher_salary_rows):
                if i == 0:
                    continue
                try:
                    sum_salary += int(row[-1])
                except ValueError:
                    pass

            return render(request, 'tools/teachers_salary_result.html', {
                'teacher_salary_rows': teacher_salary_rows,
                'sum_salary': sum_salary,
                'email': email
            })
        except TeacherNotFound:
            form.add_error(None, TEACHER_EMAIL_NOT_FOUND)
    return render(request, 'tools/teachers_salary.html', {'form': form})
