from django.urls import path

from apps.tools.views import (
    teacher_salary,
    join_to_forming_group,
    teacher_set_lesson_report,
    daily_teacher_schedule_by_interval_gsheet_export, select_discipline_for_join
)

app_name = 'tools'
urlpatterns = [
    path('lesson_report/', teacher_set_lesson_report,
         name='lesson_report'),
    path('teachers_salary/', teacher_salary,
         name='teachers_salary'),
    path('parse_teachers_schedule/', daily_teacher_schedule_by_interval_gsheet_export,
         name='daily_teacher_schedule_by_interval_gsheet_export'),
    path('join_to_forming_group/', join_to_forming_group,
         name='join_to_forming_group'),
    path('select_discipline_for_join/', select_discipline_for_join,
         name='select_discipline_for_join'),
]
