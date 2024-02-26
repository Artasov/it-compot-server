from pprint import pprint

from django.http import HttpResponse
from django.shortcuts import render

from apps.Core.services.common import acontroller
from service.hollihop.classes.custom_hollihop import CustomHHApiV2Manager
from service.hollihop.classes.exeptions import TeacherNotFound
from apps.tools.forms.other import LoadHHTeachersScheduleXLSXForm
from apps.tools.forms.teachers_salary import GetTeacherSalaryForm
from apps.tools.services.teachers_salary.funcs import (
    fetch_teacher_lessons_data_by_email,
    filter_and_aggregate_teacher_lessons
)
from apps.tools.services.teachers_shedule.funcs import handle_teachers_schedule_upload


@acontroller('Страница для записи на вводный модуль', True)
async def join_to_forming_group(request) -> HttpResponse:
    unit = await CustomHHApiV2Manager().get_ed_units(Id=19529)
    pprint(unit)
    return render(request, 'tools/join_to_forming_group.html', {
        'theme': 'light'
    })


@acontroller('Страница интервальной выгрузки занятости преподавателей за день из .xlsx', True)
async def daily_teacher_schedule_by_interval_gsheet_export(request) -> HttpResponse:
    if request.method == 'POST':
        context = await handle_teachers_schedule_upload(request)
    else:
        context = {'form': LoadHHTeachersScheduleXLSXForm()}
    return render(request, 'tools/parse_teachers_schedule.html', context)


@acontroller('Отображение зарплаты учителя по email & unipass', True)
async def teacher_salary(request) -> HttpResponse:
    form = GetTeacherSalaryForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data['email']
        try:
            filtered_lessons, sum_salary = await filter_and_aggregate_teacher_lessons(
                await fetch_teacher_lessons_data_by_email(email)
            )
            return render(request, 'tools/teachers_salary_result.html', {
                'teacher_month_lessons_list': filtered_lessons,
                'sum_salary': sum_salary,
                'email': email
            })
        except TeacherNotFound:
            form.add_error(None, "email не найден.")
    return render(request, 'tools/teachers_salary.html', {'form': form})
