from django.http import HttpResponse
from django.shortcuts import render

from apps.Core.services.base import acontroller
from apps.tools.forms.other import LoadHHTeachersScheduleXLSXForm
from apps.tools.services.teachers_salary.funcs import (
    fetch_teacher_lessons_data_by_email,
    filter_and_aggregate_teacher_lessons
)
from apps.tools.services.teachers_shedule.funcs import handle_teachers_schedule_upload


@acontroller('Страница для записи на вводный модуль', True)
async def join_to_forming_group(request) -> HttpResponse:
    return render(request, 'tools/join_to_forming_group.html', {
        'theme': 'light',
        'without_header': True
    })


@acontroller('Страница интервальной выгрузки занятости преподавателей за день из .xlsx', True)
async def daily_teacher_schedule_by_interval_gsheet_export(request) -> HttpResponse:
    if request.method == 'POST':
        context = await handle_teachers_schedule_upload(request)
    else:
        context = {'form': LoadHHTeachersScheduleXLSXForm()}
    return render(request, 'tools/parse_teachers_schedule.html', context)


@acontroller('Отображение зарплаты учителя по email & unipass', auth=True)
async def teacher_salary(request) -> HttpResponse:
    email = request.user.email
    lessons = await filter_and_aggregate_teacher_lessons(
        await fetch_teacher_lessons_data_by_email(email)
    )
    total_salary = sum(data['total_money'] for month, data in lessons.items())
    return render(request, 'tools/teachers_salary_result.html', {
        'teacher_month_lessons_list': lessons,
        'total_salary': total_salary
    })


@acontroller('Отчет за урок по email & unipass педагога', auth=True)
async def teacher_set_lesson_report(request) -> HttpResponse:
    return render(request, 'tools/set_lesson_report.html', {

    })


@acontroller('get_lasts_themes_for_unit_student')
async def get_lasts_themes_for_unit_student(request):
    from apps.tools.services.lesson_report.funcs import get_lasts_themes_for_unit_student
    await get_lasts_themes_for_unit_student()
